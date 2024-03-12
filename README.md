Upload a file to AWS S3
=======================

Upload a file to AWS S3, similar to `aws s3 cp file.txt s3://bucket/path/file.txt`,
but if the destination file (S3 object) already exists, do not overwrite it (do not upload new version).

We use this script in our CI pipelines.


Installation
------------

```shell
$ pip install 'upload-to-s3 @ https://github.com/leadhub-code/upload-to-s3/archive/v0.0.3.zip'
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


AWS IAM permissions
-------------------

Terraform example:

```terraform
resource "aws_iam_user" "example_user" {
  name = "example_user"
}

resource "aws_iam_user_policy" "example_user" {
  user = aws_iam_user.example_user.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = ["s3:GetObject*", "s3:PutObject*"]
        Resource = ["arn:aws:s3:::example-bucket/example-path/*"]
        Effect = "Allow"
      }, {
        Action = ["s3:GetBucketLocation", "s3:ListBucket"]
        Resource = ["arn:aws:s3:::example-bucket"]
        Effect = "Allow"
      },
    ]
  })
}
```
