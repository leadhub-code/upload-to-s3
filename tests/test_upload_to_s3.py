"""
Tests of upload_to_s3.main() against S3 mocked by moto - no AWS account needed.
"""

import sys

import boto3
from moto import mock_aws
from pytest import fixture, raises

import upload_to_s3
from upload_to_s3 import main, parse_s3_url, status_code_already_exists


bucket_name = 'test-bucket'


@fixture
def s3_client(monkeypatch):
    for name in 'AWS_PROFILE', 'AWS_SESSION_TOKEN', 'AWS_SECURITY_TOKEN', 'AWS_ENDPOINT_URL', 'AWS_ENDPOINT_URL_S3':
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    with mock_aws():
        client = boto3.client('s3')
        client.create_bucket(Bucket=bucket_name)
        yield client


@fixture
def temp_file(tmp_path):
    path = tmp_path / 'hello.txt'
    path.write_bytes(b'Hello, World!\n')
    return path


def run_main(monkeypatch, *args):
    """
    Runs main() with given command line arguments, returns exit status.
    """
    monkeypatch.setattr(sys, 'argv', ['upload_to_s3', *map(str, args)])
    try:
        main()
    except SystemExit as e:
        return e.code
    return 0


def read_object(s3_client, key):
    return s3_client.get_object(Bucket=bucket_name, Key=key)['Body'].read()


def test_parse_s3_url():
    assert parse_s3_url('s3://bucket/key') == ('bucket', 'key')
    assert parse_s3_url('s3://my.bucket-1/path/to/key.txt') == ('my.bucket-1', 'path/to/key.txt')
    assert parse_s3_url('s3://bucket/path/') == ('bucket', 'path/')


def test_parse_s3_url_invalid():
    for url in 's3://bucket', 's3://bucket/', 'https://bucket/key', 'bucket/key':
        with raises(SystemExit, match='Invalid S3 URL format'):
            parse_s3_url(url)


def test_version(monkeypatch, capsys):
    assert run_main(monkeypatch, '--version') == 0
    assert capsys.readouterr().out.startswith('upload_to_s3 ')


def test_upload(monkeypatch, capsys, s3_client, temp_file):
    assert run_main(monkeypatch, temp_file, f's3://{bucket_name}/path/hello.txt') == 0
    assert 'Uploaded' in capsys.readouterr().out
    obj = s3_client.get_object(Bucket=bucket_name, Key='path/hello.txt')
    assert obj['Body'].read() == b'Hello, World!\n'
    assert obj['ContentType'] == 'binary/octet-stream'


def test_upload_verbose(monkeypatch, s3_client, temp_file):
    assert run_main(monkeypatch, '--verbose', temp_file, f's3://{bucket_name}/hello.txt') == 0
    assert read_object(s3_client, 'hello.txt') == b'Hello, World!\n'


def test_upload_destination_with_trailing_slash_appends_file_name(monkeypatch, s3_client, temp_file):
    assert run_main(monkeypatch, temp_file, f's3://{bucket_name}/path/') == 0
    assert read_object(s3_client, 'path/hello.txt') == b'Hello, World!\n'


def test_upload_with_options(monkeypatch, s3_client, temp_file):
    exit_status = run_main(
        monkeypatch,
        '--content-type=text/plain',
        '--storage-class=STANDARD_IA',
        '--public',
        temp_file,
        f's3://{bucket_name}/hello.txt',
    )
    assert exit_status == 0
    obj = s3_client.get_object(Bucket=bucket_name, Key='hello.txt')
    assert obj['ContentType'] == 'text/plain'
    assert obj['StorageClass'] == 'STANDARD_IA'
    grants = s3_client.get_object_acl(Bucket=bucket_name, Key='hello.txt')['Grants']
    all_users = {'Type': 'Group', 'URI': 'http://acs.amazonaws.com/groups/global/AllUsers'}
    assert {'Grantee': all_users, 'Permission': 'READ'} in grants


def test_existing_object_is_not_overwritten(monkeypatch, capsys, s3_client, temp_file):
    s3_client.put_object(Bucket=bucket_name, Key='hello.txt', Body=b'original\n')
    assert run_main(monkeypatch, temp_file, f's3://{bucket_name}/hello.txt') == status_code_already_exists
    assert 'S3 file already exists' in capsys.readouterr().err
    assert read_object(s3_client, 'hello.txt') == b'original\n'


def test_existing_object_with_exist_ok(monkeypatch, s3_client, temp_file):
    s3_client.put_object(Bucket=bucket_name, Key='hello.txt', Body=b'original\n')
    assert run_main(monkeypatch, '--exist-ok', temp_file, f's3://{bucket_name}/hello.txt') == 0
    assert read_object(s3_client, 'hello.txt') == b'original\n'


def test_object_created_concurrently_is_not_overwritten(monkeypatch, s3_client, temp_file):
    # Simulate that the object was created after the existence check, just before the upload
    def s3_object_exists(s3, bucket_name, object_key):
        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=b'concurrent\n')
        return False

    monkeypatch.setattr(upload_to_s3, 's3_object_exists', s3_object_exists)
    assert run_main(monkeypatch, temp_file, f's3://{bucket_name}/hello.txt') == status_code_already_exists
    assert read_object(s3_client, 'hello.txt') == b'concurrent\n'


def test_file_too_large(monkeypatch, s3_client, temp_file):
    monkeypatch.setattr(upload_to_s3, 'max_file_size', 10)
    exit_status = run_main(monkeypatch, temp_file, f's3://{bucket_name}/hello.txt')
    assert exit_status.startswith('File is too large:')
    assert 'Contents' not in s3_client.list_objects_v2(Bucket=bucket_name)


def test_not_a_file(monkeypatch, s3_client, tmp_path):
    exit_status = run_main(monkeypatch, tmp_path / 'missing.txt', f's3://{bucket_name}/hello.txt')
    assert exit_status.startswith('Not a file:')


def test_nonexistent_bucket(monkeypatch, s3_client, temp_file):
    exit_status = run_main(monkeypatch, temp_file, 's3://nonexistent-bucket/hello.txt')
    assert exit_status.startswith('S3 file check failed:')
    assert 'NoSuchBucket' in exit_status
