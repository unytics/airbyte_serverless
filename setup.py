import setuptools


VERSION = '0.16'


with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()


setuptools.setup(
    name='airbyte_serverless',
    packages=['airbyte_serverless'],
    version=VERSION,
    author='Unytics',
    author_email='paul.marcombes@unytics.io',
    description='Airbyte made easy (no UI, no database, no cluster)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    download_url=f'https://github.com/unytics/airbyte_serverless/archive/refs/tags/v{VERSION}.tar.gz',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        'google-cloud-bigquery',
        'pyyaml',
        'jinja2',
        'click',
        'click-help-colors',
    ],
    entry_points={
        'console_scripts': [
            'abs = airbyte_serverless.cli:cli',
        ],
    },
)