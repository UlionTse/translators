from __future__ import annotations

import argparse
import os.path
import re
import sys
from platform import python_version

from . import __version__, translate_text, translate_html

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bring free, multiple, enjoyable translations to individuals and students."
    )

    parser.add_argument(
        "input",
        help="Raw text or path to a file to be translated"
    )

    parser.add_argument(
        "-p",
        "--provider",
        action="store",
        default="bing",
        type=str,
        dest="provider",
        help="Choose one of the supported providers. e.g. bing, google, yandex, bing etc...",
    )

    parser.add_argument(
        "-f",
        "--from",
        action="store",
        default="auto",
        type=str,
        dest="from_language",
        help="Enforce the language of origin. By default it is auto detected.",
    )

    parser.add_argument(
        "-t",
        "--to",
        action="store",
        default="en",
        type=str,
        dest="to_language",
        help="Set the destination language. Always default to english.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Translator {} - Python {}".format(
            __version__,
            python_version(),
        ),
        help="Show version information and exit.",
    )

    args = parser.parse_args(sys.argv[1:])

    # case file
    if os.path.exists(args.input):
        try:
            with open(args.input, "r", encoding="utf-8") as fp:
                content_to_translate = fp.read()
        except UnicodeDecodeError as e:
            print(f"error: file '{args.input}' is not Unicode. reason: {e}")
            return 1
        except (OSError, IOError) as e:
            print(f"error: file '{args.input}' cannot be opened. reason: {e}")
            return 2
    else:
        content_to_translate = args.input

    is_html = bool(re.findall(r"<(.*)>(.*)</(.*)>", content_to_translate))
    target_function = translate_html if is_html else translate_text

    try:
        print(
            target_function(content_to_translate, translator=args.provider, from_language=args.from_language, to_language=args.to_language)
        )
    except Exception as e:
        print(f"error: unable to translate content. reason: {e}")
        return 3

    return 0

if __name__ == "__main__":
    sys.exit(main())
