import re
import setuptools


with open('airbyte_serverless/version.py', 'r', encoding='utf-8') as fh:
    content = fh.read()
    content = content.replace('"', '').replace("'", '')
    matches = re.findall(r'VERSION\s*=\s*(\d*\.\d*)', content)
    VERSION = matches[0]


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
        'google-cloud-run',
        'google-cloud-secret-manager',
        'pyyaml',
        'jinja2',
        'click',
        'click-help-colors',
        'pipx',
    ],
    entry_points={
        'console_scripts': [
            'abs = airbyte_serverless.cli:cli',
        ],
    },
)