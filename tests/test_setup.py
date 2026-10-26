import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

import serve
import export_site
from catalog import ALL, DEFAULT_SCOPES, select_creators, validate_memberships

ROOT = Path(__file__).resolve().parents[1]


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / 'index.html').write_text('<title>Dashboard</title>')
        (self.root / 'admin.html').write_text('<title>Admin</title>')
        (self.root / 'config.json').write_text('{"creators": []}')
        self.env = self.root / '.env'
        self.env.write_text('APIFY_TOKEN=apify_api_test\n')
        workflow = self.root / '.github/workflows/refresh.yml'
        workflow.parent.mkdir(parents=True)
        workflow.write_text('on:\n  schedule:\n    - cron: "0 11 * * 0"\n  workflow_dispatch:\n')
        self.patches = [patch.object(serve, 'ROOT', self.root),
                        patch.object(serve, 'ENV_FILE', self.env),
                        patch.object(serve, 'CONFIG_FILE', self.root / 'config.json'),
                        patch.object(serve, 'ADMIN_HTML', self.root / 'admin.html')]
        for p in self.patches:
            p.start()
        self.server = serve.ReusableTCPServer(('127.0.0.1', 0), serve.AdminHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_address[1]}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def request(self, path, payload=None, content_type='application/json'):
        req = urllib.request.Request(self.base + path,
                                     data=json.dumps(payload).encode() if payload is not None else None,
                                     headers={'Content-Type': content_type})
        return urllib.request.urlopen(req)

    def test_dashboard_and_admin_are_distinct(self):
        self.assertIn(b'Dashboard', self.request('/').read())
        self.assertIn(b'Admin', self.request('/admin').read())

    def test_secrets_and_source_cannot_be_downloaded(self):
        for path in ['/.env', '/%2eenv', '/.git/config', '/serve.py', '/data/../.env']:
            with self.subTest(path=path), self.assertRaises(urllib.error.HTTPError) as exc:
                self.request(path)
            self.assertEqual(exc.exception.code, 404)

    def test_token_is_private_and_never_returned_in_state(self):
        serve.save_env_token('apify_api_new_test')
        self.assertEqual(self.env.stat().st_mode & 0o777, 0o600)
        response = self.request('/api/state').read()
        self.assertNotIn(b'apify_api_', response)
        self.assertTrue(json.loads(response)['tokenSet'])

    def test_schedule_can_be_disabled_and_reenabled_idempotently(self):
        for cron in ['off', 'off', '0 11 * * 0', '0 11 * * 0', '0 11 * * 1', 'off']:
            with self.subTest(cron=cron):
                self.assertEqual(self.request('/api/schedule', {'cron': cron}).status, 200)
                self.assertEqual(json.load(self.request('/api/schedule'))['cron'], cron)

    def test_non_json_mutation_is_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/api/token', {'token': 'apify_api_other'}, 'text/plain')
        self.assertEqual(exc.exception.code, 415)

    def test_overlapping_refresh_is_rejected(self):
        class Running:
            def poll(self):
                return None
        self.server.refresh_process = Running()
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/api/refresh', {})
        self.assertEqual(exc.exception.code, 409)

    def test_export_contains_only_dashboard_assets(self):
        (self.root / 'clips').mkdir()
        (self.root / 'clips/demo.mp4').write_bytes(b'clip')
        with patch.object(export_site, 'ROOT', self.root):
            export_site.main()
        self.assertEqual({p.name for p in (self.root / 'public').iterdir()}, {'index.html', 'clips'})
        self.assertFalse((self.root / 'public/.env').exists())

    def test_empty_feed_builds_successfully(self):
        shutil.copy2(ROOT / 'build.py', self.root / 'build.py')
        shutil.copy2(ROOT / 'catalog.py', self.root / 'catalog.py')
        (self.root / 'config.json').write_text('{"creators":[{"handle":"empty_creator"}]}')
        result = subprocess.run([sys.executable, str(self.root / 'build.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No reels yet', (self.root / 'index.html').read_text())

    def seed_lists(self):
        config = {'scopes': DEFAULT_SCOPES, 'creators': [
            {'handle': 'shared', 'scopes': ['ai-dtc', 'dtc-agencies'], 'trackingEnabled': True},
            {'handle': 'paused', 'scopes': ['ai-dtc'], 'trackingEnabled': False},
            {'handle': 'other', 'scopes': ['ai'], 'trackingEnabled': True}]}
        serve.save_config(config)
        return config

    def test_four_lists_and_membership_changes_persist(self):
        self.seed_lists()
        self.assertEqual(len(json.load(self.request('/api/state'))['scopes']), 4)
        result = json.load(self.request('/api/creators/shared', {'scopes': ['ai', 'ai'], 'trackingEnabled': False}))
        saved = next(c for c in result['creators'] if c['handle'] == 'shared')
        self.assertEqual(saved['scopes'], ['ai'])
        self.assertFalse(saved['trackingEnabled'])
        self.assertEqual(serve.load_config()['creators'][0], saved)

    def test_add_new_creator_saves_selected_list_and_prevents_case_duplicates(self):
        self.seed_lists()
        added = json.load(self.request('/api/creators', {'profile': {'handle': 'NewCreator', 'name': 'New creator'}, 'scopes': ['ai-dtc']}))
        creator = next(c for c in added['creators'] if c['handle'] == 'newcreator')
        self.assertEqual(creator['scopes'], ['ai-dtc'])
        self.assertTrue(creator['trackingEnabled'])
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/api/creators', {'profile': {'handle': 'NEWCREATOR'}, 'scopes': ['ai']})
        self.assertEqual(exc.exception.code, 409)
        self.assertEqual(len(serve.load_config()['creators']), 4)

    def test_invalid_membership_does_not_modify_file(self):
        self.seed_lists()
        before = serve.CONFIG_FILE.read_text()
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/api/creators/shared', {'scopes': ['missing']})
        self.assertEqual(exc.exception.code, 400)
        self.assertEqual(serve.CONFIG_FILE.read_text(), before)

    def test_scoped_refresh_excludes_other_lists_and_paused_creators(self):
        self.seed_lists()
        with patch.object(serve.subprocess, 'Popen') as popen:
            popen.return_value.pid = 123
            response = json.load(self.request('/api/refresh', {'scope': 'ai-dtc'}))
            self.assertEqual(response['creatorCount'], 1)
            self.assertEqual(popen.call_args.kwargs['env']['OUTLIER_SCOPE'], 'ai-dtc')

    def test_empty_list_refresh_and_unknown_scope_make_no_subprocess(self):
        self.seed_lists()
        with patch.object(serve.subprocess, 'Popen') as popen:
            for scope in ['dtc-ecommerce', 'not-a-list', []]:
                with self.subTest(scope=scope), self.assertRaises(urllib.error.HTTPError) as exc:
                    self.request('/api/refresh', {'scope': scope})
                self.assertEqual(exc.exception.code, 400)
            popen.assert_not_called()

    def test_dashboard_rebuild_does_not_start_a_refresh(self):
        with patch.object(serve.subprocess, 'run') as run, patch.object(serve.subprocess, 'Popen') as popen:
            run.return_value.returncode = 0
            self.assertTrue(json.load(self.request('/api/build', {}))['ok'])
            self.assertEqual(Path(run.call_args.args[0][-1]).name, 'build.py')
            popen.assert_not_called()


class CatalogTests(unittest.TestCase):
    def test_shared_membership_costs_one_scrape(self):
        config = {'creators': [{'handle': 'SHARED', 'scopes': ['ai-dtc', 'dtc-agencies']},
                               {'handle': 'shared', 'scopes': ['ai-dtc', 'dtc-agencies']},
                               {'handle': 'paused', 'scopes': ['ai-dtc'], 'trackingEnabled': False}]}
        self.assertEqual([c['handle'] for c in select_creators(config)], ['shared'])
        self.assertEqual(len(select_creators(config, 'dtc-agencies')), 1)
        self.assertEqual(len(select_creators(config, 'ai-dtc', tracked_only=False)), 2)

    def test_paused_data_is_available_to_dashboard(self):
        config = {'creators': [{'handle': 'paused', 'trackingEnabled': False}]}
        self.assertEqual(select_creators(config), [])
        self.assertEqual(select_creators(config, tracked_only=False)[0]['handle'], 'paused')

    def test_invalid_scope_and_handle_rejected(self):
        config = {'creators': [{'handle': '../secrets'}, {'handle': 'valid'}]}
        self.assertEqual([c['handle'] for c in select_creators(config)], ['valid'])
        with self.assertRaises(ValueError):
            select_creators(config, 'unknown')
        with self.assertRaises(ValueError):
            validate_memberships(config, 'ai-dtc')


if __name__ == '__main__':
    unittest.main()
