from subprocess import run


def test_import():
    import upload_to_s3

    assert upload_to_s3


def test_run_help():
    run(['upload_to_s3', '--help'], check=True, capture_output=True, input=b'')


def test_run_help_alias():
    run(['upload-to-s3', '--help'], check=True, capture_output=True, input=b'')


def test_run_version():
    import upload_to_s3

    cp = run(['upload_to_s3', '--version'], check=True, capture_output=True, input=b'')
    assert cp.stdout.decode().strip() == f'upload_to_s3 {upload_to_s3.__version__}'


def test_version_matches_pyproject():
    from pathlib import Path
    import tomllib

    import upload_to_s3

    pyproject = tomllib.loads((Path(__file__).parent.parent / 'pyproject.toml').read_text())
    assert upload_to_s3.__version__ == pyproject['project']['version']
