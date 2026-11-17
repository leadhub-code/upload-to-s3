Upload a file to AWS S3
=======================

Upload a file to AWS S3, similar to `aws s3 cp file.txt s3://bucket/path/file.txt`,
but if the destination file (S3 object) already exists, do not overwrite it (do not upload new version).

We use this script in our CI pipelines.


Installation
------------

Requires Python 3.11 or newer.
The package is not published on PyPI; each [GitHub Release](https://github.com/leadhub-code/upload-to-s3/releases)
contains a wheel that can be installed directly from its URL.

Using [uv](https://docs.astral.sh/uv/):

```shell
$ uv tool install https://github.com/leadhub-code/upload-to-s3/releases/download/v0.1.1/upload_to_s3-0.1.1-py3-none-any.whl
```

or run it without installing:

```shell
$ uvx --from https://github.com/leadhub-code/upload-to-s3/releases/download/v0.1.1/upload_to_s3-0.1.1-py3-none-any.whl upload-to-s3 --help
```

or run the single-file script directly (dependencies are declared in the script using
[inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/)):

```shell
$ uv run https://raw.githubusercontent.com/leadhub-code/upload-to-s3/v0.1.1/upload_to_s3.py --help
```

Using pip:

```shell
$ pip install https://github.com/leadhub-code/upload-to-s3/releases/download/v0.1.1/upload_to_s3-0.1.1-py3-none-any.whl
```

Release assets come with a `SHA256SUMS` file and a build provenance attestation,
which can be verified using the [GitHub CLI](https://cli.github.com/):

```shell
$ gh attestation verify upload_to_s3-0.1.1-py3-none-any.whl --repo leadhub-code/upload-to-s3
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
The file is uploaded using [S3 conditional write](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html),
so the object is not overwritten even if someone else creates it at the same time (e.g. a parallel CI job).
The file is uploaded in a single request (no multipart upload), so the maximum file size is 5 GiB.

Run `upload-to-s3 --help` to see all options.

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


Changelog
---------

All notable changes are listed here, newest first.
The project follows [Semantic Versioning](https://semver.org/);
while the version is `0.x.y`, a breaking change bumps the minor version.

### Unreleased

### 0.1.1 - 2026-11-17

- Fixed: an object created by someone else (e.g. a parallel CI job) between the existence check
  and the upload is no longer overwritten; the file is uploaded using S3 conditional write (`If-None-Match: *`).
- Changed: the file is uploaded in a single request (no multipart upload); files larger than 5 GiB are rejected.
- Changed: AWS errors are reported without a traceback; a 403 error mentions the `s3:ListBucket` permission.
- Changed: the caller identity (STS `GetCallerIdentity`) is logged only with `--verbose`.
- Changed: requires boto3 1.35.2 or newer.

### 0.1.0 - 2026-11-17

- **Breaking:** requires Python 3.11 or newer.
- Added: `--version` option.
- Added: `upload-to-s3` command (the old name `upload_to_s3` still works).
- Added: the script can be run directly using `uv run upload_to_s3.py`
  (dependencies are declared using PEP 723 inline script metadata).
- Added: wheel and sdist are published as GitHub Release assets, with `SHA256SUMS` and build provenance attestation.

### 0.0.3 - 2018-09-10

- Added: `--exist-ok` option (exit with status code 0 if the destination object already exists).

### 0.0.2 - 2018-09-10

- Added: if the destination ends with `/`, the source file name is appended to it.

### 0.0.1 - 2018-09-10

- Initial release.
