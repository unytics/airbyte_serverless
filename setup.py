import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='simple_airbyte',
    packages=['simple_airbyte'],
    version='0.0.1',
    author='Unytics',
    description='Airbyte made easy',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=['google-cloud-bigquery', 'pyyaml']
)