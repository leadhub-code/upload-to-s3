Upload a file to AWS S3
=======================

Upload a file to AWS S3, similar to `aws s3 cp file.txt s3://bucket/path/file.txt`,
but if the destination file (S3 object) already exists, do not overwrite it (do not upload new version).

We use this script in our CI pipelines.


Installation
------------

Requires Python 3.11 or newer.

Using [uv](https://docs.astral.sh/uv/):

```shell
$ uv tool install 'git+https://github.com/leadhub-code/upload-to-s3@v0.0.3'
```

or run it without installing:

```shell
$ uvx --from 'git+https://github.com/leadhub-code/upload-to-s3@v0.0.3' upload-to-s3 --help
```

Using pip:

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
$ upload-to-s3 --public --content-type text/plain foo.txt s3://bucket/path/foo.txt
```

If the destination object already exists, it is not overwritten and `upload-to-s3` exits with status code 3
(or 0 when `--exist-ok` is used).

Note: `--public` sets the `public-read` ACL. Buckets with ACLs disabled
(Object Ownership "Bucket owner enforced", the default for buckets created since April 2023)
reject such uploads.


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


Development
-----------

```shell
$ uv sync                  # create .venv with dev dependencies
$ uv run pytest tests      # E2E tests run only when TEST_AWS_S3_PREFIX and AWS credentials are set
$ uv run ruff check
$ uv run ruff format
```

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).
