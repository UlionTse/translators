from distutils.core import setup
from setuptools import find_packages


PACKAGE = "translate_api"
NAME = "translate_api"
DESCRIPTION = "Translate API for Python3 used Google.The default Google server for China, you can switch to use."
AUTHOR = "UlionTse"
AUTHOR_EMAIL = "shinalone@outlook.com"
URL = "https://github.com/shinalone/translate_api"
VERSION = __import__(PACKAGE).__version__

with open('readme.rst') as file:
    long_description = file.read()

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="MIT",
    url=URL,
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ],
    keywords=['translate','translate_api'],
    python_requires='>=3',
    install_requires=[
        'requests>=2.9.1',
        'PyExecJS>=1.2.0',
        'fake-useragent>=0.1.7'
    ],
    zip_safe=False,
)
