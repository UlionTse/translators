# coding=utf-8
# author=UlionTse

"""
Copyright (C) 2017  UlionTse

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Email: uliontse@outlook.com

translators  Copyright (C) 2017  UlionTse
This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
This is free software, and you are welcome to redistribute it
under certain conditions; type `show c' for details.
"""

import os
import sys
import argparse

from translators import __version__, __author__
from translators import translate_text, translate_html


def translate_cli() -> None:
    parser = argparse.ArgumentParser(
        description='Translators(fanyi for CLI) is a library that aims to bring free, multiple, enjoyable translations '
                    'to individuals and students in Python.'
    )
    parser.add_argument(
        'input',
        default='',
        help='Inputs to be translated.'
    )
    parser.add_argument(
        '--text_file',
        action='store',
        default='',
        type=str,
        dest='text_file',
        help='path to a file to be translated',
    )
    parser.add_argument(
        '--translator',
        action='store',
        default='alibaba',
        type=str,
        dest='translator',
        help='eg: bing, google, yandex, etc... A comma-separated list (eg: google,bing) is tried in order as fallbacks.',
    )
    parser.add_argument(
        '--preserve',
        action='append',
        default=None,
        type=str,
        dest='preserve',
        metavar='REGEX',
        help='regex of spans to keep untranslated; repeatable.',
    )
    parser.add_argument(
        '--from',
        action='store',
        default='auto',
        type=str,
        dest='from_language',
        help='from_language, default `auto` detected.',
    )
    parser.add_argument(
        '--to',
        action='store',
        default='en',
        type=str,
        dest='to_language',
        help='to_language, default `en`.',
    )
    parser.add_argument(
        '--is_html',
        action='store',
        default=0,
        type=int,
        dest='is_html',
        help='is_html, default `0`.',
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'Translators(fanyi for CLI) - Version: {__version__} - Author: {__author__}',
        help='show version and author information.',
    )
    args = parser.parse_args()

    if args.text_file != '' and os.path.exists(args.text_file):
        try:
            with open(file=args.text_file, mode='r', encoding='utf-8') as file:
                query_text = file.read()
        except Exception as e:
            print(str(e))
            sys.exit(1)
    else:
        query_text = args.input.strip()

    try:
        translate_fn = translate_html if bool(args.is_html) else translate_text
        extra_kwargs = {'preserve': args.preserve} if args.preserve and not args.is_html else {}
        result = translate_fn(
            query_text=query_text,
            translator=args.translator,
            from_language=args.from_language,
            to_language=args.to_language,
            **extra_kwargs,
        )
        print(result)
    except Exception as e:
        print(str(e))
        sys.exit(1)
    return


if __name__ == '__main__':
    translate_cli()
