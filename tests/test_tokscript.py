import io
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import refresh
import tokscript
import tokscript_backfill as backfill
from storage import write_json


class TokScriptTests(unittest.TestCase):
    def seed(self, root):
        write_json(root/'config.json', {'creators': [{'handle': 'one'}]})
        write_json(root/'data/one_posts.json', {'items': [
            {'shortCode': 'new', 'videoPlayCount': 999, 'timestamp': '2026-10-20T12:00:00Z'},
            {'shortCode': 'local', 'transcript': 'Local draft', 'transcription': {'provider': 'mlx-whisper'}},
            {'shortCode': 'done', 'transcript': 'Saved', 'transcription': {'provider': 'tokscript'}}]})

    def test_webvtt_and_srt_become_readable_speech(self):
        self.assertEqual(backfill.plain_transcript('WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nFish &amp; chips\n\n00:00:02.000 --> 00:00:03.000\n2026'), 'Fish & chips 2026')
        self.assertEqual(backfill.plain_transcript('1\n00:00:00,000 --> 00:00:02,000\nFirst sentence.'), 'First sentence.')
        self.assertEqual(backfill.plain_transcript([{'text': 'Hello'}, {'text': 'world'}]), 'Hello world')

    def test_exact_reel_matching_rejects_other_hosts_and_supports_post_urls(self):
        self.assertEqual(backfill.shortcode('https://www.instagram.com/p/Ab_C-2/?utm=a'), 'Ab_C-2')
        self.assertIsNone(backfill.shortcode('https://malicious.example/reel/new/'))
        self.assertIsNone(backfill.shortcode('https://www.instagram.com/creator/'))

    def test_import_updates_local_draft_preserves_current_stats_and_other_creators(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.seed(root)
            saved = backfill.saved_reels(root)
            rows = [{'source_url': 'https://www.instagram.com/reel/new/', 'transcript': 'Actual speech', 'views': None, 'publish_date': 'WRONG'},
                    {'source_url': 'https://www.instagram.com/reel/local/', 'transcript': 'TokScript version'},
                    {'source_url': 'https://www.instagram.com/reel/not_saved/', 'transcript': 'Unrelated'}]
            backfill.import_rows(root, rows, saved, 'library')
            posts = {p['shortCode']: p for p in json.loads((root/'data/one_posts.json').read_text())['items']}
            self.assertEqual(len(posts), 3)
            self.assertEqual(posts['new']['transcript'], 'Actual speech')
            self.assertEqual(posts['new']['videoPlayCount'], 999)
            self.assertEqual(posts['new']['timestamp'], '2026-10-20T12:00:00Z')
            self.assertEqual(posts['local']['transcript'], 'TokScript version')
            self.assertEqual(posts['done']['transcript'], 'Saved')

    def test_unavailable_service_preserves_existing_local_speech_and_marks_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.seed(root)
            backfill.mark_unavailable(root, ['https://www.instagram.com/reel/local/', 'https://www.instagram.com/reel/new/'], backfill.saved_reels(root))
            posts = {p['shortCode']: p for p in json.loads((root/'data/one_posts.json').read_text())['items']}
            self.assertEqual(posts['local']['transcript'], 'Local draft')
            self.assertEqual(posts['local']['transcriptionAttempt']['provider'], 'tokscript')
            self.assertEqual(posts['new']['transcription']['status'], 'error')

    def test_punctuation_only_result_is_no_speech_and_does_not_loop(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.seed(root)
            found = backfill.import_rows(root, [{'source_url': 'https://www.instagram.com/reel/new/', 'transcript': '.'}], backfill.saved_reels(root), 'library')
            post = backfill.saved_reels(root)['new']['post']
            self.assertEqual(found, {'new'})
            self.assertEqual(post['transcript'], '')
            self.assertEqual(post['transcription']['status'], 'no_speech')
            self.assertFalse(backfill.needs_tokscript(post))

    def test_stats_refresh_keeps_saved_transcript(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(refresh, 'DATA', Path(temp)), patch.object(refresh, 'CREATORS', ['one']):
            now = datetime.now(timezone.utc).isoformat()
            refresh.save_posts('one', [{'shortCode': 'new', 'timestamp': now, 'transcript': 'Speech',
                                       'transcription': {'provider': 'tokscript', 'status': 'ready'}}])
            refresh.merge_pass1_stats([{'ownerUsername': 'one', 'shortCode': 'new', 'timestamp': now,
                                       'videoPlayCount': 150, 'transcript': None}])
            post = refresh.load_existing_posts('one')[0]
            self.assertEqual(post['transcript'], 'Speech')
            self.assertEqual(post['transcription']['provider'], 'tokscript')

    def test_refresh_uses_tokscript_and_never_falls_back_to_apify(self):
        with patch.object(refresh, 'load_key', return_value='sk_test'), patch.object(refresh.subprocess, 'run') as run, patch.object(refresh, 'start_actor') as paid:
            refresh.refresh_transcripts()
            paid.assert_not_called()
            self.assertTrue(run.call_args.args[0][1].endswith('tokscript_backfill.py'))
        with patch.object(refresh, 'load_key', return_value=None), patch.object(refresh, 'start_actor') as paid:
            with self.assertRaises(RuntimeError):
                refresh.refresh_transcripts()
            paid.assert_not_called()

    def test_job_resume_polls_existing_id_without_resubmission(self):
        class Client:
            def call(self, name, **kwargs):
                self.asserted_name = name
                return {'status': 'complete', 'result_key': 'rk_existing', 'completed': 1, 'total': 1}
        client = Client()
        job = {'job_id': 'ts_existing', 'urls': ['https://www.instagram.com/reel/new/']}
        with tempfile.TemporaryDirectory() as temp, patch.object(backfill, 'download_export', return_value=[{'source_url': job['urls'][0], 'transcript': 'Saved'}]):
            rows, status = backfill.poll_export(client, job, Path(temp), lambda: None)
        self.assertTrue(job['exported'])
        self.assertEqual(client.asserted_name, 'get_job_status')
        self.assertEqual(len(rows), 1)

    def test_failed_remote_job_is_terminal_so_other_retries_can_proceed(self):
        class Client:
            def call(self, *args, **kwargs):
                return {'status': 'failed'}
        job = {'job_id': 'ts_failed', 'urls': ['https://www.instagram.com/reel/new/']}
        with tempfile.TemporaryDirectory() as temp:
            rows, _ = backfill.poll_export(Client(), job, Path(temp), lambda: None)
        self.assertEqual(rows, [])
        self.assertTrue(job['terminalFailed'])

    def test_lost_submission_response_blocks_duplicates_then_reconciles_library(self):
        class Client:
            submissions = 0
            ready = False
            def call(self, name, **kwargs):
                if name == 'get_user_library':
                    return {'count': 2 if self.ready else 0, 'result_key': 'rk_library', 'pagination': {'has_next': False}}
                if name == 'submit_transcript_job':
                    self.submissions += 1
                    raise TimeoutError('Accepted remotely, response lost')
                raise AssertionError('Unexpected call '+name)
        client = Client()
        with tempfile.TemporaryDirectory() as temp, patch.object(backfill, 'TokScript', return_value=client):
            root = Path(temp); self.seed(root)
            with self.assertRaisesRegex(RuntimeError, 'not confirmed'):
                backfill.backfill(root)
            receipt = json.loads((root/'.cache/tokscript/jobs.json').read_text())[0]
            self.assertEqual(receipt['status'], 'submission_uncertain')
            with self.assertRaisesRegex(RuntimeError, 'awaiting reconciliation'):
                backfill.backfill(root)
            self.assertEqual(client.submissions, 1)
            client.ready = True
            rows = [{'source_url': 'https://www.instagram.com/reel/'+sc+'/', 'transcript': 'Recovered speech'} for sc in ['new', 'local']]
            with patch.object(backfill, 'download_export', return_value=rows):
                result = backfill.backfill(root)
            self.assertEqual(result['requested'], 0)
            self.assertEqual(client.submissions, 1)
            receipt = json.loads((root/'.cache/tokscript/jobs.json').read_text())[0]
            self.assertEqual(receipt['status'], 'reconciled')

    def test_export_download_does_not_forward_mcp_credentials(self):
        class Client:
            def call(self, *args, **kwargs):
                return {'download_url': 'https://pub-example.r2.dev/export.json'}
        def fetch(request, **kwargs):
            self.assertIsNone(request.get_header('Authorization'))
            self.assertEqual(request.get_header('User-agent'), 'Mozilla/5.0')
            return io.BytesIO(b'[{"source_url":"https://www.instagram.com/reel/new/","transcript":"Speech"}]')
        with tempfile.TemporaryDirectory() as temp, patch.object(backfill.urllib.request, 'urlopen', side_effect=fetch):
            rows = backfill.download_export(Client(), 'rk_test', Path(temp)/'export.json')
            self.assertEqual(len(rows), 1)

    def test_mcp_client_handles_json_and_sse_responses(self):
        client = object.__new__(tokscript.TokScript)
        client.headers = {}; client.sequence = 0
        class Response(io.BytesIO):
            headers = {'Mcp-Session-Id': 'session'}
        replies = [Response(b'{"jsonrpc":"2.0","id":1,"result":{"ok":true}}'),
                   Response(b'event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"ok":true}}\n\n')]
        with patch.object(tokscript.urllib.request, 'urlopen', side_effect=replies):
            self.assertEqual(client.rpc('tools/list'), {'ok': True})
            self.assertEqual(client.rpc('tools/list'), {'ok': True})
            self.assertEqual(client.headers['Mcp-Session-Id'], 'session')

    def test_mcp_tool_errors_are_not_imported_as_transcript_text(self):
        client = object.__new__(tokscript.TokScript)
        with patch.object(client, 'rpc', return_value={'isError': True, 'content': [{'type': 'text', 'text': 'Daily limit reached'}]}):
            with self.assertRaises(RuntimeError):
                client.call('submit_transcript_job', urls=['https://www.instagram.com/reel/new/'])


if __name__ == '__main__':
    unittest.main()
