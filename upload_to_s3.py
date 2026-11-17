#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "boto3>=1.35.2",  # S3 conditional writes (IfNoneMatch)
# ]
# ///

import argparse
from logging import DEBUG, INFO, basicConfig, getLogger
from pathlib import Path
import re
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError


__version__ = '0.1.1'

logger = getLogger(__name__)


# "Unix programs generally use 2 for command line syntax errors"
# so let's skip 2 and use 3
status_code_already_exists = 3

# Maximum object size for a single PutObject request (S3 limit).
# Multipart upload is not used, because it does not support conditional write via s3transfer
# and this tool is meant for small files.
max_file_size = 5 * 1024**3


def main():
    p = argparse.ArgumentParser(
        description='Upload a file to AWS S3. If the destination object already exists, it is not overwritten.',
        epilog=f'Exit status is {status_code_already_exists} if the destination object already exists '
        '(unless --exist-ok is used).',
    )
    p.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    p.add_argument('--region', help='AWS region (default: from AWS configuration)')
    p.add_argument('--public', action='store_true', help='set public-read ACL')
    p.add_argument('--storage-class', default='STANDARD', help='S3 storage class (default: %(default)s)')
    p.add_argument('--content-type', help='Content-Type of the object (default: binary/octet-stream)')
    p.add_argument('--verbose', '-v', action='store_true', help='enable debug logging')
    p.add_argument('--exist-ok', action='store_true', help='exit with status 0 if the destination already exists')
    p.add_argument('path', help='local file to upload')
    p.add_argument(
        'destination',
        help='S3 URL in the form s3://bucket/key; if it ends with "/", the local file name is appended',
    )
    args = p.parse_args()
    setup_logging(verbose=args.verbose)
    path = Path(args.path)
    if not path.is_file():
        sys.exit(f'Not a file: {path}')
    if path.stat().st_size > max_file_size:
        sys.exit(f'File is too large: {path} (maximum size is {max_file_size} bytes)')
    bucket_name, object_key = parse_s3_url(args.destination)
    if object_key.endswith('/'):
        object_key += path.name
    if args.verbose:
        log_caller_identity(region=args.region)
    s3 = boto3.client('s3', region_name=args.region)
    if s3_object_exists(s3, bucket_name, object_key):
        exit_already_exists(bucket_name, object_key, exist_ok=args.exist_ok)
    extra_args = {
        'StorageClass': args.storage_class,
    }
    if args.public:
        extra_args['ACL'] = 'public-read'
    if args.content_type:
        extra_args['ContentType'] = args.content_type
    if not upload_file(s3, path, bucket_name, object_key, extra_args):
        # The object was created by someone else between our check and upload
        exit_already_exists(bucket_name, object_key, exist_ok=args.exist_ok)
    print(f'Uploaded {path} to bucket {bucket_name} key {object_key}')


def parse_s3_url(s3_url):
    m = re.match(r'^s3://([a-zA-Z0-9._-]+)/(.+)$', s3_url)
    if not m:
        sys.exit(f'Invalid S3 URL format: {s3_url}')
    bucket_name, object_key = m.groups()
    return bucket_name, object_key


def log_caller_identity(region):
    try:
        identity = boto3.client('sts', region_name=region).get_caller_identity()
        logger.debug('AWS caller identity: %s', identity['Arn'])
    except Exception as e:
        logger.debug('Could not retrieve AWS caller identity: %s', e)


def s3_object_exists(s3, bucket_name, object_key):
    """
    Returns True if S3 object exists, False if it does not (404).
    Exits the program on any other error.
    """
    try:
        s3.head_object(Bucket=bucket_name, Key=object_key)
    except ClientError as e:
        logger.debug('head_object error response: %r', e.response)
        code = e.response.get('Error', {}).get('Code')
        if code in ('404', 'NoSuchKey', 'NotFound'):
            return False
        hint = ''
        if code in ('403', 'AccessDenied'):
            hint = ' (note: without s3:ListBucket permission S3 returns 403 Forbidden also for nonexistent objects)'
        sys.exit(f'S3 file check failed: bucket {bucket_name} key {object_key}: {e}{hint}')
    except BotoCoreError as e:
        sys.exit(f'S3 file check failed: bucket {bucket_name} key {object_key}: {e}')
    return True


def upload_file(s3, path, bucket_name, object_key, extra_args):
    """
    Uploads the file to S3 unless the object already exists.
    Returns True if the file was uploaded, False if the object already exists.
    Exits the program on any other error.
    """
    logger.info('upload_file extra_args: %r', extra_args)
    try:
        # Conditional write: S3 rejects the request if the object already exists,
        # so an object created concurrently by someone else is never overwritten.
        with path.open('rb') as f:
            s3.put_object(Bucket=bucket_name, Key=object_key, Body=f, IfNoneMatch='*', **extra_args)
    except ClientError as e:
        if e.response.get('Error', {}).get('Code') == 'PreconditionFailed':
            logger.debug('put_object error response: %r', e.response)
            return False
        sys.exit(f'Failed to upload {path} to bucket {bucket_name} key {object_key}: {e}')
    except BotoCoreError as e:
        sys.exit(f'Failed to upload {path} to bucket {bucket_name} key {object_key}: {e}')
    return True


def exit_already_exists(bucket_name, object_key, exist_ok):
    print(f'S3 file already exists: bucket {bucket_name} key {object_key}', file=sys.stderr)
    sys.exit(0 if exist_ok else status_code_already_exists)


def setup_logging(verbose):
    basicConfig(format='%(asctime)s %(name)-20s %(levelname)5s: %(message)s', level=DEBUG if verbose else INFO)
    getLogger('boto3').setLevel(INFO)
    getLogger('botocore').setLevel(INFO)


if __name__ == '__main__':
    main()
