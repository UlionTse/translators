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
import re
import sys
import platform
import argparse

from . import __version__, translate_text, translate_html


def translate_cli() -> None:
    parser = argparse.ArgumentParser(
        description='Translators(fanyi for CLI) is a library that aims to bring free, multiple, enjoyable translations '
                    'to individuals and students in Python.'
    )
    parser.add_argument(
        'input',
        help='Raw text or path to a file to be translated.'
    )
    parser.add_argument(
        '--translator',
        action='store',
        default='bing',
        type=str,
        dest='translator',
        help='eg: bing, google, yandex, etc...',
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
        '--version',
        action='version',
        version='Translators(fanyi for CLI) {} - Python {}'.format(__version__, platform.python_version()),
        help='show version information.',
    )
    args = parser.parse_args()

    if os.path.exists(args.input):
        try:
            with open(args.input, 'r', encoding='utf-8') as file:
                query_text = file.read()
        except Exception as e:
            print(str(e))
            sys.exit(1)
    else:
        query_text = args.input

    is_html = bool(re.findall(r'<(.*)>(.*)</(.*)>', query_text))
    fn = translate_html if is_html else translate_text

    try:
        print(fn(query_text, translator=args.translator, from_language=args.from_language, to_language=args.to_language))
    except Exception as e:
        print(str(e))
        sys.exit(1)

    return


if __name__ == '__main__':
    translate_cli()
