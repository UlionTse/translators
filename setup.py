# coding=utf-8
# author=UlionTse

import re
import pathlib
from setuptools import setup, find_packages


NAME = "translators"
PACKAGE = "translators"

AUTHOR = "UlionTse"
AUTHOR_EMAIL = "shinalone@outlook.com"
HOMEPAGE_URL = "https://github.com/uliontse/translators"
DESCRIPTION = "Translators is a library which aims to bring free, multiple, enjoyable translation to individuals and students in Python."
LONG_DESCRIPTION = pathlib.Path('README.md').read_text(encoding='utf-8')
VERSION = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', pathlib.Path('translators/__init__.py').read_text(), re.M).group(1)


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    package_dir={"translators": "translators"},
    url=HOMEPAGE_URL,
    project_urls={
        'Source': 'https://github.com/UlionTse/translators',
        'Changelog': 'https://github.com/UlionTse/translators/blob/master/change_log.txt',
        'Documentation': 'https://github.com/UlionTse/translators/blob/master/README.md',
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords=[
        'translate', 'translate_html',
        'alibaba', 'argos', 'baidu', 'bing', 'caiyun', 'deepl', 'google', 'iciba', 'iflytek', 'iflyrec',
        'itranslate', 'lingvanex', 'mglip', 'modernMt', 'myMemory', 'niutrans', 'papago', 'qqFanyi', 'qqTranSmart',
        'reverso', 'sogou', 'translateCom', 'utibet', 'volcEngine', 'yandex', 'youdao',
    ],
    install_requires=[
        'requests>=2.28.1',
        'PyExecJS>=1.5.1',
        'lxml>=4.9.1',
        'tqdm>=4.65.0',
        'pathos>=0.2.9',
        'cryptography>=38.0.1',
    ],
    python_requires='>=3.8',
    extras_require={'pypi': ['build>=0.8.0', 'twine>=4.0.1']},
    zip_safe=False,
)
