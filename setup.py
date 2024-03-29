from setuptools import setup, find_packages

setup(
    name='repo2prompt',
    version='0.1.0',
    description='Github repo -> prompt string',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'requests>=2.20.0',
    ],
)