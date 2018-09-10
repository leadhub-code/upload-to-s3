Upload a file to AWS S3
=======================

There is awscli with command `aws s3 cp file.txt s3://bucket/path`, but it has no option to not overwrite the destination file if it already exists.

[CircleCI](https://circleci.com/gh/leadhub-code/upload-to-s3)


Installation
------------

```shell
$ pip install 'https://github.com/leadhub-code/upload-to-s3/archive/v0.0.3.zip#egg=upload-to-s3==0.0.3'
```


Usage
-----

```shell
upload_to_s3 --public --content-type text/plain foo.txt s3://bucket/path/foo.txt
```
