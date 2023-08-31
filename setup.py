import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='simple_airbyte',                  # This is the name of the package
    packages=['simple_airbyte'],
    version='0.0.1',                        # The initial release version
    author='Unytics',                       # Full name of the author
    description='Airbyte made easy',
    long_description=long_description,      # Long description read from the the readme file
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],                                      # Information to filter the project on PyPi website
    python_requires='>=3.6',                # Minimum version requirement of the package
    install_requires=[]                     # Install other dependencies if any
)