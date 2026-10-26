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
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import serve
import export_site
from catalog import ALL, DEFAULT_SCOPES, select_creators, validate_memberships, parse_handles

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
        self.env.write_text(self.env.read_text() + 'TOKSCRIPT_API_KEY=sk_private_test\n')
        serve.save_env_token('apify_api_new_test')
        self.assertEqual(self.env.stat().st_mode & 0o777, 0o600)
        response = self.request('/api/state').read()
        self.assertNotIn(b'apify_api_', response)
        self.assertNotIn(b'sk_private_test', response)
        self.assertIn('TOKSCRIPT_API_KEY=sk_private_test', self.env.read_text())
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

    def test_transcript_only_job_does_not_require_apify_token(self):
        self.seed_lists()
        self.env.unlink()
        class Job:
            pid = 42
            def poll(self):
                return None
        with patch.object(serve, 'load_tokscript_key', return_value='sk_test'), patch.object(serve.subprocess, 'Popen', return_value=Job()) as start:
            result = json.load(self.request('/api/transcripts', {'scope': 'ai-dtc'}))
            self.assertTrue(result['ok'])
            command = start.call_args.args[0]
            self.assertEqual(command[0], sys.executable)
            self.assertTrue(command[2].endswith('tokscript_backfill.py'))
            self.assertIn('--build', command)
            self.assertEqual(command[command.index('--handles') + 1:], ['shared'])

    def test_transcript_job_requires_tokscript_and_rejects_overlap(self):
        self.seed_lists()
        with patch.object(serve, 'load_tokscript_key', return_value=None):
            with self.assertRaises(urllib.error.HTTPError) as exc:
                self.request('/api/transcripts', {'scope': 'ai-dtc'})
            self.assertEqual(exc.exception.code, 400)
        class Running:
            def poll(self):
                return None
        self.server.refresh_process = Running()
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/api/transcripts', {'scope': 'ai-dtc'})
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

    def test_bulk_import_saves_without_waiting_for_profile_job(self):
        self.seed_lists()
        with patch.object(serve, 'get_jobs') as jobs:
            jobs.return_value.submit.return_value = {'id': 'slow', 'status': 'running'}
            data = json.load(self.request('/api/creators/import', {'handles': '@One @two, @ONE', 'scopes': ['ai']}))
            self.assertEqual(data['saved'], ['one', 'two'])
            self.assertEqual(data['job']['status'], 'running')
            self.assertEqual(next(c for c in data['creators'] if c['handle'] == 'one')['scopes'], ['ai'])
            self.assertEqual(json.load(self.request('/api/state'))['creators'], data['creators'])

    def test_bulk_import_is_idempotent_and_budget_errors_do_not_lose_handles(self):
        self.seed_lists()
        with patch.object(serve, 'get_jobs') as jobs:
            jobs.return_value.submit.side_effect = ValueError('Daily lookup budget reached')
            for _ in range(2):
                response = json.load(self.request('/api/creators/import', {'handles': ['new'], 'scopes': ['ai-dtc']}))
            self.assertIn('budget', response['warning'])
            self.assertEqual(sum(c['handle'] == 'new' for c in response['creators']), 1)

    def test_enrichment_preserves_membership_and_does_not_resurrect_deleted_creators(self):
        self.seed_lists()
        serve.apply_profile_details(['shared', 'removed'], [
            {'handle': 'shared', 'name': 'Enriched name', 'profileStatus': 'ready', 'scopes': ['ai'], 'trackingEnabled': False},
            {'handle': 'removed', 'name': 'Deleted', 'profileStatus': 'ready'}])
        creators = serve.load_config()['creators']
        shared = next(c for c in creators if c['handle'] == 'shared')
        self.assertEqual(shared['scopes'], ['ai-dtc', 'dtc-agencies'])
        self.assertTrue(shared['trackingEnabled'])
        self.assertFalse(any(c['handle'] == 'removed' for c in creators))

    def test_concurrent_saves_do_not_lose_creators(self):
        with patch.object(serve, 'get_jobs') as jobs:
            jobs.return_value.submit.return_value = {'id': 'pending', 'status': 'queued'}
            def add(number):
                return json.load(self.request('/api/creators/import', {'handles': [f'creator{number}'], 'scopes': ['ai']}))
            with ThreadPoolExecutor(max_workers=6) as pool:
                list(pool.map(add, range(12)))
        self.assertEqual(len(serve.load_config()['creators']), 12)

    def test_new_name_search_returns_a_job_immediately(self):
        with patch.object(serve, 'get_jobs') as jobs:
            jobs.return_value.submit.return_value = {'id': 'pending', 'status': 'running', 'message': 'Still searching'}
            response = self.request('/api/search?q=Alice')
            self.assertEqual(response.status, 202)
            self.assertEqual(json.load(response)['job']['id'], 'pending')

    def test_admin_remains_available_during_a_long_request(self):
        entered, release = threading.Event(), threading.Event()
        def slow_build(*args, **kwargs):
            entered.set()
            release.wait(2)
            class Result:
                returncode = 0
            return Result()
        with patch.object(serve.subprocess, 'run', side_effect=slow_build):
            request_thread = threading.Thread(target=lambda: self.request('/api/build', {}).close())
            request_thread.start()
            try:
                self.assertTrue(entered.wait(1))
                with urllib.request.urlopen(self.base+'/api/state', timeout=1) as response:
                    self.assertEqual(response.status, 200)
            finally:
                release.set()
                request_thread.join(2)


class CatalogTests(unittest.TestCase):
    def test_pasted_handles_support_urls_case_and_dotted_names(self):
        self.assertEqual(parse_handles('@Kallaway, @sferro.ai\nhttps://www.instagram.com/KALLAWAY/ @samin_yasar12'),
                         ['kallaway', 'sferro.ai', 'samin_yasar12'])
        for invalid in ['https://evil.example/alice', '@../private', '']:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_handles(invalid)
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
