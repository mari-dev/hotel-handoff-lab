import os
import unittest
from unittest.mock import patch
from judge_lambda import handler


class JudgeAccessTests(unittest.TestCase):
    def event(self, **headers):
        return {'headers': {**headers},
                'rawPath':'/api/requests',
                'requestContext':{'domainName':'demo.lambda-url.eu-north-1.on.aws','http':{'method':'GET'}}}

    def setUp(self):
        self.env=patch.dict(os.environ, {'JUDGE_PASSWORD':'synthetic-test-password'})
        self.env.start();self.addCleanup(self.env.stop)
        self.backend=patch('judge_lambda.local_server')
        self.local=self.backend.start();self.addCleanup(self.backend.stop)

    def test_cross_origin_request_rejected_even_with_correct_password(self):
        self.assertEqual(handler(self.event(origin='https://attacker.invalid'),None)['statusCode'],403)
        self.local.assert_not_called()

    def test_missing_config_fails_closed(self):
        with patch.dict(os.environ, {'JUDGE_PASSWORD':''}):
            self.assertEqual(handler(self.event(),None)['statusCode'],503)
        self.local.assert_not_called()

    def test_oversized_body_rejected_before_backend(self):
        event=self.event();event['body']='x'*20001
        self.assertEqual(handler(event,None)['statusCode'],413)
        self.local.assert_not_called()

    def test_private_file_path_is_not_forwarded(self):
        event=self.event();event['rawPath']='/.env'
        self.assertEqual(handler(event,None)['statusCode'],404)
        self.local.assert_not_called()
