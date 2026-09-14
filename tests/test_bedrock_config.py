import os
import unittest
from unittest.mock import patch

from bedrock_config import ai_configured, make_model


class BedrockConfigTests(unittest.TestCase):
    def test_unconfigured_fails_without_network(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(ai_configured())
            with self.assertRaises(ValueError):
                make_model()

    def test_profile_session_is_passed_without_conflicting_region(self):
        with patch.dict(os.environ, {'AWS_PROFILE': 'hotel-handoff-lab'}, clear=True), \
             patch('boto3.Session') as session, patch('strands.models.BedrockModel') as model:
            self.assertTrue(ai_configured())
            make_model()
            session.assert_called_once_with(profile_name='hotel-handoff-lab', region_name='eu-north-1')
            model.assert_called_once_with(boto_session=session.return_value,
                model_id='amazon.nova-lite-v1:0', max_tokens=1200, temperature=0)

    def test_cross_region_profile_rejected(self):
        with patch.dict(os.environ, {'AWS_PROFILE': 'hotel-handoff-lab',
                                    'HANDOFF_MODEL_ID': 'eu.amazon.nova-lite-v1:0'}, clear=True):
            with self.assertRaises(ValueError):
                make_model()
