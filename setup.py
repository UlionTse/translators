from distutils.core import setup
from setuptools import find_packages

PACKAGE = "translate_api"
NAME = "translate_api"
DESCRIPTION = "Translate API for Python3 used Google.The default Google server for China, you can change."
AUTHOR = "UlionTse"
AUTHOR_EMAIL = "shinalone@outlook.com"
URL = "https://github.com/shinalone/translate_api"
VERSION = __import__(PACKAGE).__version__

with open('README.md') as file:
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
        "Development Status :: 2 - Production/stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ],
    zip_safe=False,
)
