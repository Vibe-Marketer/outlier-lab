import unittest

from reel_coverage import summarize_coverage


class CoverageTests(unittest.TestCase):
    def test_loaded_missing_and_collaboration_only_are_distinct(self):
        rows = [
            {'inputUrl': 'https://www.instagram.com/alice/', 'ownerUsername': 'alice', 'shortCode': 'one'},
            {'inputUrl': 'https://www.instagram.com/alice/', 'ownerUsername': 'alice', 'shortCode': 'one'},
            {'inputUrl': 'https://www.instagram.com/bob/', 'ownerUsername': 'publisher', 'shortCode': 'two', 'coauthorProducers': [{'username': 'bob'}]},
            {'inputUrl': 'https://www.instagram.com/carol/', 'error': 'no_items'},
        ]
        result = summarize_coverage(['alice', 'bob', 'carol', 'missing'], rows, 40, '2026-10-26')
        self.assertEqual(result['alice']['authoredReels'], 1)
        self.assertEqual(result['bob']['authoredReels'], 0)
        self.assertEqual(result['bob']['collaborations'], 1)
        self.assertEqual(result['bob']['status'], 'collaborations_only')
        self.assertEqual(result['carol']['errors'], ['no_items'])
        self.assertEqual(result['missing']['status'], 'no_reels_returned')
        self.assertEqual(result['missing']['rowsReturned'], 0)

    def test_tagged_person_is_not_counted_as_a_collaborator(self):
        rows = [{'inputUrl': 'https://www.instagram.com/alice/', 'ownerUsername': 'publisher',
                 'shortCode': 'one', 'taggedUsers': [{'username': 'alice'}], 'coauthorProducers': None}]
        self.assertEqual(summarize_coverage(['alice'], rows, 40)['alice']['collaborations'], 0)
