from logging import DEBUG, INFO, basicConfig, getLogger
import os
import sys


# If we are running in venv, but venv/bin is not in the path, then we want to add it
# because we want to run the installed script in e2e tests
if f'{sys.prefix}/bin' not in os.environ['PATH']:
    os.environ['PATH'] = f"{sys.prefix}/bin:{os.environ['PATH']}"


basicConfig(
    format='%(asctime)s %(name)s %(levelname)5s: %(message)s',
    level=DEBUG)

getLogger('boto3').setLevel(INFO)
getLogger('botocore').setLevel(INFO)
