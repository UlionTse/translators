__version__ = "6.0.4"
__author__ = "UlionTse"

from translators.server import (
    translators_pool,
    get_languages,
    get_region_of_server,
    refresh_keyed_engines as refresh_keyed_engines_with_sync,
)
from translators.server import (
    translate_text as translate_text_with_sync,
    translate_html as translate_html_with_sync,
    preaccelerate_and_speedtest as preaccelerate_and_speedtest_with_sync,
)
from translators.server_async import (
    translate_text as translate_text_with_async,
    translate_html as translate_html_with_async,
    preaccelerate_and_speedtest as preaccelerate_and_speedtest_with_async,
    close as close_with_async,
    refresh_keyed_engines as refresh_keyed_engines_with_async,
)


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



def refresh_keyed_engines(path=None):
    """Re-read credentials for keyed engines in both servers; returns the configured names."""
    refresh_keyed_engines_with_async(path)
    return refresh_keyed_engines_with_sync(path)


__all__ = (
    "refresh_keyed_engines",
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
