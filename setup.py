from setuptools import setup

setup(
    name="Internal Deployment Script",
    version='0.0.1',
    packages=[
        "deploy"
    ],
    install_requires=[
        "docker",
    ],
    test_requires=[
        "pytest"
    ]
)
