#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='upload-to-s3',
    version='0.0.1',
    description='Upload a file to AWS S3',
    classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    py_modules=['upload_to_s3'],
    install_requires=[
        'boto3',
    ],
    entry_points={
        'console_scripts': [
            'upload_to_s3=upload_to_s3:main',
        ],
    })
