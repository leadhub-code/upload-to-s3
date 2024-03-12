'''
Configured Github Actions secrets:

- TEST_AWS_ACCESS_KEY_ID will become env variable AWS_ACCESS_KEY_ID
- TEST_AWS_SECRET_ACCESS_KEY will become env variable AWS_SECRET_ACCESS_KEY
- TEST_AWS_S3_PREFIX will become env variable TEST_AWS_S3_PREFIX
'''

import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from logging import getLogger
import os
from pytest import fixture, skip
import re
import requests
from secrets import token_urlsafe
from subprocess import run


logger = getLogger(__name__)


@fixture
def s3_prefix():
    try:
        return os.environ['TEST_AWS_S3_PREFIX']
    except KeyError:
        skip('TEST_AWS_S3_PREFIX not configured')


@fixture
def s3_client():
    return boto3.client('s3')


def test_upload(s3_prefix, tmp_path, s3_client):
    now = datetime.now(timezone.utc)
    temp_file = tmp_path / 'test_upload.txt'
    temp_file.write_bytes(b'Hello, World!\n')

    bucket_name, key_prefix = re.match(r'^s3://([a-zA-Z0-9._-]+)/(.+)$', s3_prefix).groups()
    full_key = f"{key_prefix.strip('/')}/test_upload.{now:%Y%m%dT%H%M%SZ}.{token_urlsafe()[:7]}.txt".strip('/')
    logger.debug('bucket_name: %r full_key: %r', bucket_name, full_key)

    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=full_key)
    except ClientError as e:
        logger.debug('ClientError: %r response: %r', e, e.response)
        assert e.response['Error']['Code'] == 'NoSuchKey'
    else:
        raise AssertionError(f"Object already exists: {obj}")

    cmd = [
        'upload_to_s3',
        '--verbose',
        '--storage-class', 'STANDARD',
        str(temp_file),
        f's3://{bucket_name}/{full_key}',
    ]
    logger.debug('Running cmd: %r', cmd)
    run(cmd, check=True, input=b'')

    obj = s3_client.get_object(Bucket=bucket_name, Key=full_key)
    assert obj['ContentType'] == 'binary/octet-stream'
    assert obj['Body'].read() == b'Hello, World!\n'

    # Test failing when file already exists
    temp_file.write_bytes(b'This should not be uploaded\n')

    cmd = [
        'upload_to_s3',
        '--verbose',
        str(temp_file),
        f's3://{bucket_name}/{full_key}',
    ]
    logger.debug('Running cmd: %r', cmd)
    result = run(cmd, input=b'')
    assert result.returncode == 3

    obj = s3_client.get_object(Bucket=bucket_name, Key=full_key)
    assert obj['ContentType'] == 'binary/octet-stream'
    assert obj['Body'].read() == b'Hello, World!\n'

    # Test not failing when file already exists
    cmd = [
        'upload_to_s3',
        '--verbose',
        '--exist-ok',
        str(temp_file),
        f's3://{bucket_name}/{full_key}',
    ]
    logger.debug('Running cmd: %r', cmd)
    run(cmd, check=True, input=b'')

    obj = s3_client.get_object(Bucket=bucket_name, Key=full_key)
    assert obj['ContentType'] == 'binary/octet-stream'
    assert obj['Body'].read() == b'Hello, World!\n'


def test_upload_with_content_type_and_public(s3_prefix, tmp_path, s3_client):
    now = datetime.now(timezone.utc)
    temp_file = tmp_path / 'test_upload.txt'
    temp_file.write_bytes(b'Hello, World!\n')

    bucket_name, key_prefix = re.match(r'^s3://([a-zA-Z0-9._-]+)/(.+)$', s3_prefix).groups()
    full_key = f"{key_prefix.strip('/')}/test_upload.{now:%Y%m%dT%H%M%SZ}.{token_urlsafe()[:7]}.txt".strip('/')
    logger.debug('bucket_name: %r full_key: %r', bucket_name, full_key)

    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=full_key)
    except ClientError as e:
        logger.debug('ClientError: %r response: %r', e, e.response)
        assert e.response['Error']['Code'] == 'NoSuchKey'
    else:
        raise AssertionError(f"Object already exists: {obj}")

    cmd = [
        'upload_to_s3',
        '--verbose',
        '--storage-class', 'STANDARD',
        '--content-type', 'text/plain',
        '--public',
        str(temp_file),
        f's3://{bucket_name}/{full_key}',
    ]
    logger.debug('Running cmd: %r', cmd)
    run(cmd, check=True, input=b'')

    obj = s3_client.get_object(Bucket=bucket_name, Key=full_key)
    assert obj['ContentType'] == 'text/plain'
    assert obj['Body'].read() == b'Hello, World!\n'

    r = requests.get(f'https://{bucket_name}.s3.amazonaws.com/{full_key}')
    assert r.status_code == 200
    assert r.headers['Content-Type'] == 'text/plain'
    assert r.text == 'Hello, World!\n'
