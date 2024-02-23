# coding=utf-8
# author=UlionTse

import re
import pathlib
import setuptools


NAME = "translators"
PACKAGE = "translators"

AUTHOR = "UlionTse"
AUTHOR_EMAIL = "uliontse@outlook.com"
HOMEPAGE_URL = "https://github.com/uliontse/translators"
DESCRIPTION = "Translators is a library that aims to bring free, multiple, enjoyable translations to individuals and students in Python."
LONG_DESCRIPTION = pathlib.Path('README.md').read_text(encoding='utf-8')
VERSION_TEXT = pathlib.Path(f'{PACKAGE}/__init__.py').read_text(encoding='utf-8')
VERSION = re.compile('^__version__\\s*=\\s*[\'"]([^\'"]*)[\'"]', re.MULTILINE).search(VERSION_TEXT).group(1)


setuptools.setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="GPLv3",
    packages=setuptools.find_packages(),
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
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords=[
        'translate', 'translate_text', 'translate_html',
        'alibaba', 'apertium', 'argos', 'baidu', 'bing',
        'caiyun', 'cloudTranslation', 'deepl', 'elia', 'google',
        'hujiang', 'iciba', 'iflytek', 'iflyrec', 'itranslate',
        'judic', 'languageWire', 'lingvanex', 'mglip', 'mirai',
        'modernMt', 'myMemory', 'niutrans', 'papago', 'qqFanyi',
        'qqTranSmart', 'reverso', 'sogou', 'sysTran', 'tilde',
        'translateCom', 'translateMe', 'utibet', 'volcEngine', 'yandex',
        'yeekit', 'youdao',
    ],
    install_requires=[
        'requests>=2.29.0',
        'PyExecJS>=1.5.1',
        'lxml>=4.9.1',
        'tqdm>=4.65.0',
        'pathos>=0.2.9',
        'cryptography>=42.0.4',
    ],
    python_requires='>=3.8',
    extras_require={'pypi': ['build>=0.8.0', 'twine>=4.0.1']},
    zip_safe=False,
)
