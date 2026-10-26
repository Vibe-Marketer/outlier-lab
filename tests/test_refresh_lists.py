import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import refresh


class ScopedRefreshTests(unittest.TestCase):
    def test_scoped_pruning_preserves_other_lists_and_paused_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ['data', 'clips', 'thumbs']:
                (root / name).mkdir()
            config = {'creators': [
                {'handle': 'selected', 'scopes': ['ai-dtc']},
                {'handle': 'other', 'scopes': ['ai']},
                {'handle': 'paused', 'trackingEnabled': False}]}
            for handle in ['selected', 'other', 'paused']:
                (root / 'data' / f'{handle}_posts.json').write_text(json.dumps({'items': [{'shortCode': handle}]}))
                (root / 'clips' / f'{handle}.mp4').write_bytes(b'clip')
            (root / 'clips' / 'expired.mp4').write_bytes(b'expired')
            with patch.multiple(refresh, CONFIG=config, CREATORS=['selected'], DATA=root/'data', CLIPS=root/'clips', THUMBS=root/'thumbs'):
                refresh.prune_old_assets()
            self.assertEqual({p.stem for p in (root/'clips').iterdir()}, {'selected', 'other', 'paused'})

    def test_collaborator_views_do_not_enter_authored_baseline(self):
        with patch.object(refresh, 'start_actor') as start, patch.object(refresh, 'wait_for_run') as wait, patch.object(refresh, 'fetch_dataset') as fetch:
            start.return_value = {'id': 'test'}
            wait.return_value = {'status': 'SUCCEEDED', 'defaultDatasetId': 'test'}
            fetch.return_value = [
                {'shortCode': 'authored', 'ownerUsername': 'selected'},
                {'shortCode': 'collaboration', 'ownerUsername': 'different_owner', 'inputUrl': 'https://www.instagram.com/selected'},
                {'error': 'no_items'}]
            with tempfile.TemporaryDirectory() as temp, patch.object(refresh, 'DATA', Path(temp)), patch.object(refresh, 'CREATORS', ['selected']):
                self.assertEqual([r['shortCode'] for r in refresh.pass1_stats_refresh()], ['authored'])

    def test_empty_list_does_not_start_an_actor(self):
        with patch.object(refresh, 'CREATORS', []), patch.object(refresh, 'start_actor') as start:
            refresh.main()
            start.assert_not_called()


if __name__ == '__main__':
    unittest.main()
