"""Explicit local authentication configuration; no calls during health checks."""
import os


def ai_configured():
    return bool(os.getenv('AWS_PROFILE') or os.getenv('AWS_BEARER_TOKEN_BEDROCK')
                or os.getenv('AWS_LAMBDA_FUNCTION_NAME'))


def make_model():
    import boto3
    from strands.models import BedrockModel
    if not ai_configured():
        raise ValueError('Set AWS_PROFILE or AWS_BEARER_TOKEN_BEDROCK before starting the server')
    region = os.getenv('AWS_REGION', 'eu-north-1')
    model_id = os.getenv('HANDOFF_MODEL_ID', 'amazon.nova-lite-v1:0')
    if region != 'eu-north-1' or model_id.startswith(('eu.', 'us.', 'global.', 'apac.')):
        raise ValueError('This project requires in-region inference in eu-north-1')
    session = boto3.Session(profile_name=os.getenv('AWS_PROFILE'), region_name=region)
    return BedrockModel(boto_session=session, model_id=model_id,
                        max_tokens=1200, temperature=0)
