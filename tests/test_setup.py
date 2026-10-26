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
        (self.root / 'config.json').write_text('{"creators":[{"handle":"empty_creator"}]}')
        result = subprocess.run([sys.executable, str(self.root / 'build.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No reels yet', (self.root / 'index.html').read_text())


if __name__ == '__main__':
    unittest.main()
