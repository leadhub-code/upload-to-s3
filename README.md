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

You need to have AWS credentials prepared:

- create file `.aws/credentials` (for example using `aws configure`), or
- set env variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
  - for example on CircleCI see "Project settings" -> "Environment Variables"
- or use any other way documented in [boto3 Credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html)



```shell
$ upload_to_s3 --public --content-type text/plain foo.txt s3://bucket/path/foo.txt
```


