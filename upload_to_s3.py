#!/usr/bin/env python3

import argparse
import boto3
import logging
from pathlib import Path
import re
import sys


logger = logging.getLogger(__name__)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--region')
    p.add_argument('--public', action='store_true')
    p.add_argument('--storage-class', default='STANDARD')
    p.add_argument('--content-type')
    p.add_argument('--verbose', '-v', action='store_true')
    p.add_argument('path')
    p.add_argument('destination', help='URL in the form: s3://bucket/key')
    args = p.parse_args()
    setup_logging(verbose=args.verbose)
    if args.path.endswith('/'):
        sys.exit('destination URL must not end with /')
    if not Path(args.path).is_file():
        sys.exit('Not a file: {}'.format(args.path))
    m = re.match(r'^s3://([^/]+)/(.+)$', args.destination)
    if not m:
        sys.exit('Invalid S3 URL format: {}'.format(args.destination))
    bucket_name, object_key = m.groups()
    s3 = boto3.resource('s3', region_name=args.region)
    obj = s3.Object(bucket_name=bucket_name, key=object_key)
    # check if S3 file exists
    try:
        obj.load()
    except Exception as e:
        logger.debug('obj.load exception: %r', e)
        try:
            code = str(e.response['Error']['Code'])
        except Exception as e2:
            logger.debug('e.response exception: %r', e2)
            code = None
        if code != '404':
            sys.exit('S3 file check failed: {!r}'.format(e))
    else:
        print('S3 file already exists: {}'.format(obj), file=sys.stderr)
        # "Unix programs generally use 2 for command line syntax errors"
        # so let's skip 2 and use 3
        sys.exit(3)
    extra_args = {
        'StorageClass': args.storage_class,
    }
    if args.public:
        extra_args['ACL'] = 'public-read'
    if args.content_type:
        extra_args['ContentType'] = args.content_type
    logger.info('upload_file extra_args: %r', extra_args)
    s3.meta.client.upload_file(args.path, bucket_name, object_key, ExtraArgs=extra_args)
    logger.debug('Upload done')


def setup_logging(verbose):
    from logging import DEBUG, INFO
    logging.basicConfig(
        format='%(asctime)s %(name)-20s %(levelname)5s: %(message)s',
        level=DEBUG if verbose else INFO)


if __name__ == '__main__':
    main()
