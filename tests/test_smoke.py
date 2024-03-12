from subprocess import run


def test_import():
    import upload_to_s3
    assert upload_to_s3


def test_run_help():
    run(['upload_to_s3', '--help'], check=True, capture_output=True, input=b'')
