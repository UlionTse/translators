# coding=utf-8
# author=UlionTse

import os
from setuptools import setup, find_packages


PACKAGE = "translators"
NAME = "translators"
DESCRIPTION = "Translators is a library which aims to bring free, multiple, enjoyable translation to individuals " \
              "and students in Python."
AUTHOR = "UlionTse"
AUTHOR_EMAIL = "shinalone@outlook.com"
URL = "https://github.com/uliontse/translators"

try:
    VERSION = __import__(PACKAGE).__version__
except:
    os.system('pip install --upgrade -r requirements.txt')
    VERSION = __import__(PACKAGE).__version__

with open('README.md', 'r', encoding='utf-8') as file:
    long_description = file.read()

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="MIT",
    url=URL,
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        # "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords=['translate', 'translator', 'fanyi', 'translate_html', 'Google', 'Yandex', 'Bing',
              'Baidu', 'Alibaba', 'Tencent', 'Youdao', 'Sogou', 'Iciba', 'Iflytek', 'Deepl',
              'Caiyun', 'Argos', 'Reverso', 'Itranslate', 'TranslateCom'],
    install_requires=[
        'requests>=2.27.1',
        'PyExecJS>=1.5.1',
        'lxml>=4.8.0',
        'loguru>=0.6.0',
        'pathos>=0.2.8',
    ],
    zip_safe=False,
)
