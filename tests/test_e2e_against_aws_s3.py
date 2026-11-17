"""
End-to-end tests against real AWS S3.

They run only when env variable TEST_AWS_S3_PREFIX (s3://bucket/prefix/) and AWS credentials are set.

Configured Github Actions secrets:

- TEST_AWS_ACCESS_KEY_ID will become env variable AWS_ACCESS_KEY_ID
- TEST_AWS_SECRET_ACCESS_KEY will become env variable AWS_SECRET_ACCESS_KEY
- TEST_AWS_S3_PREFIX will become env variable TEST_AWS_S3_PREFIX
"""

from datetime import UTC, datetime
from logging import getLogger
import os
import re
from secrets import token_urlsafe
from subprocess import run

import boto3
from botocore.exceptions import ClientError
from pytest import fixture, skip
import requests


logger = getLogger(__name__)


@fixture
def s3_prefix():
    # GitHub Actions sets missing secrets (e.g. in pull requests from forks) to an empty string
    s3_prefix = os.environ.get('TEST_AWS_S3_PREFIX')
    if not s3_prefix:
        skip('TEST_AWS_S3_PREFIX not configured')
    return s3_prefix


@fixture
def s3_client():
    return boto3.client('s3')


@fixture
def s3_destination(s3_prefix, s3_client):
    """
    Returns unique (bucket_name, key) of an S3 object that does not exist yet.
    """
    bucket_name, key_prefix = re.match(r'^s3://([a-zA-Z0-9._-]+)/(.+)$', s3_prefix).groups()
    now = datetime.now(UTC)
    key = f'{key_prefix.strip("/")}/test_upload.{now:%Y%m%dT%H%M%SZ}.{token_urlsafe()[:7]}.txt'.strip('/')
    logger.debug('bucket_name: %r key: %r', bucket_name, key)
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=key)
    except ClientError as e:
        logger.debug('ClientError: %r response: %r', e, e.response)
        assert e.response['Error']['Code'] == 'NoSuchKey'
    else:
        raise AssertionError(f'Object already exists: {obj}')
    return bucket_name, key


def upload_to_s3(*args):
    cmd = ['upload_to_s3', '--verbose', *map(str, args)]
    logger.debug('Running cmd: %r', cmd)
    return run(cmd, input=b'').returncode


def test_upload(tmp_path, s3_client, s3_destination):
    bucket_name, key = s3_destination
    temp_file = tmp_path / 'test_upload.txt'
    temp_file.write_bytes(b'Hello, World!\n')

    assert upload_to_s3('--storage-class', 'STANDARD', temp_file, f's3://{bucket_name}/{key}') == 0

    obj = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert obj['ContentType'] == 'binary/octet-stream'
    assert obj['Body'].read() == b'Hello, World!\n'

    # Test failing when file already exists
    temp_file.write_bytes(b'This should not be uploaded\n')
    assert upload_to_s3(temp_file, f's3://{bucket_name}/{key}') == 3

    obj = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert obj['ContentType'] == 'binary/octet-stream'
    assert obj['Body'].read() == b'Hello, World!\n'

    # Test not failing when file already exists
    assert upload_to_s3('--exist-ok', temp_file, f's3://{bucket_name}/{key}') == 0

    obj = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert obj['ContentType'] == 'binary/octet-stream'
    assert obj['Body'].read() == b'Hello, World!\n'


def test_upload_with_content_type_and_public(tmp_path, s3_client, s3_destination):
    bucket_name, key = s3_destination
    temp_file = tmp_path / 'test_upload.txt'
    temp_file.write_bytes(b'Hello, World!\n')

    exit_status = upload_to_s3(
        '--storage-class=STANDARD',
        '--content-type=text/plain',
        '--public',
        temp_file,
        f's3://{bucket_name}/{key}',
    )
    assert exit_status == 0

    obj = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert obj['ContentType'] == 'text/plain'
    assert obj['Body'].read() == b'Hello, World!\n'

    r = requests.get(f'https://{bucket_name}.s3.amazonaws.com/{key}')
    assert r.status_code == 200
    assert r.headers['Content-Type'] == 'text/plain'
    assert r.text == 'Hello, World!\n'
