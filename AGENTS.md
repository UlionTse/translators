# Notes for coding agents

`translators` is a Python library and CLI (`fanyi`) that calls free web translation endpoints and, optionally, official APIs with the user's own key.

- Using it: `translators.translate_text(text, translator=['google', 'bing'], to_language='zh', preserve='code')`. A list of engines is a fallback chain; `preserve` keeps code spans, paths and identifiers untranslated. See "Engine Fallback and Preserve" in README.md.
- Setting up keyed engines (DeepL API, Azure, Google Cloud, Baidu, Alibaba, Caiyun, Youdao, NiuTrans, Volcengine): follow docs/configure-keys.md. Do not ask users to paste keys into chat; give them the credential-store command for their OS (macOS keychain, Windows Credential Manager or Linux Secret Service) or let them edit the credentials file themselves.
- Tests: `python -m unittest discover -s tests` (offline; set `translators_default_region=EN` to skip the network region lookup, the tests do this themselves).
- Code layout: engines live in `translators/server.py` (sync) and `translators/server_async.py` (async twin). Both files are over 6,000 lines; search them rather than reading them whole. Keyed engines are in `translators/keyed.py`, credentials in `translators/credentials.py`, retired engines and aliases in `translators/retired.py`.
