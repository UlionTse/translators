__version__ = "6.0.4"
__author__ = "UlionTse"

from importlib import import_module

from translators.server import (
    translators_pool,
    get_languages,
    get_region_of_server,
)
from translators.server import (
    translate_text as translate_text_with_sync,
    translate_html as translate_html_with_sync,
    preaccelerate_and_speedtest as preaccelerate_and_speedtest_with_sync,
)


def _get_async_function(function_name):
    try:
        server_async = import_module('translators.server_async')
    except ModuleNotFoundError as exc:
        if exc.name == 'aiohttp':
            raise ImportError(
                "Async translation requires the 'async' extra: "
                "pip install 'translators[async]'"
            ) from exc
        raise
    return getattr(server_async, function_name)


async def translate_text_with_async(*args, **kwargs):
    return await _get_async_function('translate_text')(*args, **kwargs)


async def translate_html_with_async(*args, **kwargs):
    return await _get_async_function('translate_html')(*args, **kwargs)


async def preaccelerate_and_speedtest_with_async(*args, **kwargs):
    return await _get_async_function('preaccelerate_and_speedtest')(*args, **kwargs)


def translate_text(*args, **kwargs):
    if kwargs.get('if_use_async', False):
        return translate_text_with_async(*args, **kwargs)
    return translate_text_with_sync(*args, **kwargs)


def translate_html(*args, **kwargs):
    if kwargs.get('if_use_async', False):
        return translate_html_with_async(*args, **kwargs)
    return translate_html_with_sync(*args, **kwargs)


def preaccelerate_and_speedtest(*args, **kwargs):
    if kwargs.get('if_use_async', False):
        return preaccelerate_and_speedtest_with_async(*args, **kwargs)
    return preaccelerate_and_speedtest_with_sync(*args, **kwargs)


async def close_with_async(*args, **kwargs):
    return await _get_async_function('close')(*args, **kwargs)


__all__ = (
    "__version__",
    "__author__",
    "translate_text",
    "translate_html",
    "translators_pool",
    "get_languages",
    "get_region_of_server",
    "preaccelerate_and_speedtest",
    "close_with_async",
)
