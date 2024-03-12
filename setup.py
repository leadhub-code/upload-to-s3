#!/usr/bin/env python3

from setuptools import setup

setup(
    name='upload-to-s3',
    version='0.0.3',
    description='Upload a file to AWS S3',
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
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
