# coding=utf-8
# author=UlionTse

"""
Engines whose free web endpoint no longer works, and names that now point at a working engine.

A retired engine is left out of `translators_pool`; asking for it raises TranslatorError with the
reason. Its class stays in server.py so it can be revived if the provider reopens the endpoint.
Only engines that fail the same way from any network belong here (offline site, lost domain,
mandatory captcha). Engines blocked only from some regions stay in the pool.
"""

from typing import Dict

__all__ = ('RETIRED_TRANSLATORS', 'TRANSLATOR_ALIASES', 'resolve')

# name -> why it was retired (checked 2026-10-29)
RETIRED_TRANSLATORS: Dict[str, str] = {
    'judic': 'judic.io no longer hosts a translator; the domain now redirects to an unrelated site.',
    'niutrans': 'niutrans.com requires a solved Geetest captcha token on every translate call.',
    'tilde': 'translate.tilde.com now redirects to translate.tilde.ai, whose API is key-gated; '
             'the old letsmt.eu endpoints answer 400. Not ported yet.',
    'translateMe': 'translateme.network dropped its free web translator (the tm_my_action AJAX handler is gone).',
}

# old name -> engine that replaces it
TRANSLATOR_ALIASES: Dict[str, str] = {
    'iflytek': 'iflyrec',  # fanyi.xfyun.cn translation now needs a logged-in account; iflyrec is iFlytek's open one
    'qqFanyi': 'qqTranSmart',  # fanyi.qq.com now needs a solved TCaptcha ticket; TranSmart is Tencent's open one
}


def resolve(name: str) -> str:
    """
    :param name: engine name as given by the caller.
    :return: the engine name to use (alias target, or `name` unchanged).
    :raise LookupError: `name` is retired; the message carries the reason.
    """
    if name in RETIRED_TRANSLATORS:
        raise LookupError('{}() is retired: {}'.format(name, RETIRED_TRANSLATORS[name]))
    return TRANSLATOR_ALIASES.get(name, name)
