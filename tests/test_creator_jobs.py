import hashlib
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

from creator_jobs import ProfileJobs
from serve import normalize_profile
from storage import write_json


class ProfileJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'jobs.json'
        self.managers = []

    def tearDown(self):
        for manager in self.managers:
            manager.close()
        self.temp.cleanup()

    def manager(self, request, **kwargs):
        manager = ProfileJobs(self.path, lambda: 'private_test_credential', normalize_profile,
                              kwargs.pop('apply_profiles', Mock()), Mock(), request=request,
                              poll_seconds=.002, **kwargs)
        self.managers.append(manager)
        return manager

    def wait_done(self, manager, job_id):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            job = manager.get(job_id)
            if job['status'] in {'succeeded', 'failed'}:
                return job
            time.sleep(.005)
        self.fail('Background job did not complete')

    def test_submit_is_nonblocking_and_duplicate_queries_start_one_actor(self):
        entered, release = threading.Event(), threading.Event()
        starts = []
        def request(path, token, body=None, **params):
            if path.startswith('acts/'):
                starts.append(params)
                entered.set()
                release.wait(1)
                return {'data': {'id': 'run', 'status': 'RUNNING'}}
            if path.startswith('actor-runs/'):
                return {'data': {'id': 'run', 'status': 'SUCCEEDED', 'defaultDatasetId': 'data', 'usageTotalUsd': .003}}
            return [{'username': 'alice', 'fullName': 'Alice', 'private': False}]
        manager = self.manager(request)
        try:
            first = manager.submit('profiles', ['alice'])
            self.assertTrue(entered.wait(1))
            self.assertEqual(manager.submit('profiles', ['alice'])['id'], first['id'])
            self.assertNotEqual(manager.get(first['id'])['status'], 'succeeded')
            self.assertEqual(len(starts), 1)
        finally:
            release.set()
        done = self.wait_done(manager, first['id'])
        self.assertEqual(done['status'], 'succeeded')
        self.assertEqual(manager.submit('profiles', ['alice'])['id'], first['id'])
        self.assertEqual(len(starts), 1)
        self.assertEqual(starts[0]['maxTotalChargeUsd'], .10)
        self.assertNotIn('private_test_credential', self.path.read_text())

    def test_restart_resumes_existing_run_without_new_actor(self):
        job = {'id': 'old', 'key': 'existing-key', 'kind': 'profiles', 'value': ['alice'],
               'status': 'running', 'runId': 'existing', 'createdAt': time.time(), 'capUsd': .10}
        write_json(self.path, {'old': job})
        calls = []
        def request(path, token, body=None, **params):
            calls.append(path)
            if path.startswith('actor-runs/'):
                return {'data': {'id': 'existing', 'status': 'SUCCEEDED', 'defaultDatasetId': 'data', 'usageTotalUsd': .003}}
            if path.startswith('acts/'):
                raise AssertionError('Restart submitted another paid actor')
            return [{'username': 'alice'}]
        manager = self.manager(request)
        self.assertEqual(self.wait_done(manager, 'old')['status'], 'succeeded')
        self.assertFalse(any(path.startswith('acts/') for path in calls))

    def test_uncertain_submission_is_not_retried_on_restart(self):
        job = {'id': 'uncertain', 'key': 'x', 'kind': 'profiles', 'value': ['alice'],
               'status': 'starting', 'createdAt': time.time(), 'capUsd': .10}
        write_json(self.path, {'uncertain': job})
        request = Mock()
        manager = self.manager(request)
        self.assertEqual(manager.get('uncertain')['status'], 'failed')
        request.assert_not_called()

    def test_daily_caps_include_queued_reservations(self):
        release = threading.Event()
        def request(*args, **kwargs):
            release.wait(1)
            return {'data': {'id': 'run', 'status': 'RUNNING'}}
        manager = self.manager(request, daily_cap=.20)
        try:
            manager.submit('profiles', ['one'])
            manager.submit('profiles', ['two'])
            with self.assertRaises(ValueError):
                manager.submit('profiles', ['three'])
            self.assertEqual(len(manager.jobs), 2)
        finally:
            manager.stop.set()
            release.set()

    def test_slow_actor_uses_repeated_short_polls(self):
        polls = 0
        def request(path, token, body=None, **params):
            nonlocal polls
            if path.startswith('acts/'):
                return {'data': {'id': 'run', 'status': 'RUNNING'}}
            if path.startswith('actor-runs/'):
                polls += 1
                return {'data': {'id': 'run', 'status': 'RUNNING' if polls < 60 else 'SUCCEEDED', 'defaultDatasetId': 'data'}}
            return [{'username': 'alice'}]
        manager = self.manager(request)
        job = manager.submit('search', 'Alice')
        self.assertEqual(self.wait_done(manager, job['id'])['status'], 'succeeded')
        self.assertEqual(polls, 60)

    def test_retry_after_poll_failure_reuses_run_instead_of_paying_again(self):
        starts = []
        fail = True
        def request(path, token, body=None, **params):
            nonlocal fail
            if path.startswith('acts/'):
                starts.append(path)
                return {'data': {'id': 'run', 'status': 'RUNNING'}}
            if path.startswith('actor-runs/'):
                if fail:
                    fail = False
                    raise RuntimeError('Temporary result delivery failure')
                return {'data': {'id': 'run', 'status': 'SUCCEEDED', 'defaultDatasetId': 'data'}}
            return [{'username': 'alice'}]
        manager = self.manager(request)
        job = manager.submit('profiles', ['alice'])
        self.assertEqual(self.wait_done(manager, job['id'])['status'], 'failed')
        retried = manager.submit('profiles', ['alice'])
        self.assertEqual(retried['id'], job['id'])
        self.assertEqual(self.wait_done(manager, job['id'])['status'], 'succeeded')
        self.assertEqual(len(starts), 1)
