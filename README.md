Upload a file to AWS S3
=======================

There is awscli with command `aws s3 cp file.txt s3://bucket/path`, but it has no option to not overwrite the destination file if it already exists.

[CircleCI](https://circleci.com/gh/leadhub-code/upload-to-s3)
