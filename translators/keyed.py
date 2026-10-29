# coding=utf-8
# author=UlionTse

"""
Official-API engines that need the user's own key. Each joins `translators_pool` only when its
required credentials are configured (see credentials.py). Sync implementations; the async server
runs them in a thread.
"""

import threading
import time
from typing import Callable, Dict, List, Optional, Tuple, Type, Union

import requests

from translators import credentials

__all__ = ('KeyedEngineError', 'KeyedEngine', 'KEYED_CLASSES', 'KEYED_PRIORITY', 'KEY_COOLDOWN', 'KeyRotation', 'KEYS', 'register', 'DeeplApi', 'Azure', 'GoogleCloud',
           'BaiduApi', 'YoudaoApi', 'CaiyunApi', 'NiutransApi', 'AliyunApi', 'VolcEngineApi',
           'aliyun_rpc_sign', 'volc_sign')

KEYED_CLASSES: Dict[str, Type['KeyedEngine']] = {}

# Order of keyed engines inside a chain's 'keyed' token: quality first, providers that bill overage
# automatically (googleCloud, baiduApi, aliyunApi) last.
KEYED_PRIORITY = ('deeplApi', 'volcEngineApi', 'azure', 'caiyunApi', 'youdaoApi', 'niutransApi',
                  'googleCloud', 'baiduApi', 'aliyunApi')

TRAD_ZH = ('zh-TW', 'zh-tw', 'zh-Hant', 'zh-CHT', 'zh-HK', 'zh-hk')
SIMP_ZH = ('zh', 'zh-CN', 'zh-cn', 'zh-CHS', 'zh-Hans', 'zh-Hans_CN', 'cn', 'chi', 'Chinese')


class KeyedEngineError(Exception):
    """Provider rejected the call; the next key set is tried. `cooldown` > 0 rests this key that long (quota, auth, rate limit)."""

    def __init__(self, message: str = '', cooldown: float = 0.0):
        super().__init__(message)
        self.cooldown = cooldown


# Seconds a key rests after these HTTP statuses: auth / payment / DeepL quota (456) for an hour, rate limit for a minute.
KEY_COOLDOWN = {401: 3600.0, 402: 3600.0, 403: 3600.0, 456: 3600.0, 429: 60.0}
DEFAULT_PRIORITY = 10
META_FIELDS = ('priority',)  # key-set fields that are not credentials


class KeyRotation:
    """
    Picks the key-set order for each call: lower `priority` first; key sets that share a priority take
    turns (round robin); a key set resting after a quota, auth or rate-limit error goes to the end.
    """

    def __init__(self):
        self._turn: Dict[Tuple[str, int], int] = {}
        self._until: Dict[Tuple[str, str], float] = {}
        self._lock = threading.Lock()

    @staticmethod
    def priority(fields: Dict[str, str]) -> int:
        try:
            return int(fields.get('priority', DEFAULT_PRIORITY))
        except ValueError:
            return DEFAULT_PRIORITY

    def order(self, engine: str, sets: List[Tuple[str, Dict[str, str]]]) -> List[Tuple[str, Dict[str, str]]]:
        out, now = [], time.monotonic()
        with self._lock:
            for prio in sorted({self.priority(f) for _, f in sets}):
                tier = [s for s in sets if self.priority(s[1]) == prio]
                turn = self._turn.get((engine, prio), 0)
                self._turn[(engine, prio)] = turn + 1
                k = turn % len(tier)
                out.extend(tier[k:] + tier[:k])
            resting = [s for s in out if self._until.get((engine, s[0]), 0) > now]
        return [s for s in out if s not in resting] + resting

    def rest(self, engine: str, label: str, seconds: float) -> None:
        with self._lock:
            self._until[(engine, label)] = time.monotonic() + seconds

    def ok(self, engine: str, label: str) -> None:
        with self._lock:
            self._until.pop((engine, label), None)

    def reset(self) -> None:
        with self._lock:
            self._turn.clear()
            self._until.clear()


KEYS = KeyRotation()


def register(name: str, required: Tuple[str, ...], optional: Tuple[str, ...] = ()) -> Callable:
    def deco(cls):
        cls.name, cls.required, cls.optional = name, required, optional
        KEYED_CLASSES[name] = cls
        credentials.KEYED_ENGINES[name] = (required, optional)
        return cls
    return deco


class KeyedEngine:
    name: str = ''
    required: Tuple[str, ...] = ()
    optional: Tuple[str, ...] = ()
    zh_code, zh_hant_code, auto_code = 'zh', 'zh-TW', None  # None: omit source for auto-detect

    def __init__(self):
        self.session = None
        self.language_map = None  # kept for get_languages(); keyed engines validate server-side

    def code(self, lang: str) -> Optional[str]:
        if lang in (None, '', 'auto'):
            return self.auto_code
        if lang in TRAD_ZH:
            return self.zh_hant_code
        if lang in SIMP_ZH:
            return self.zh_code
        return lang

    def cred(self, field: str, kwargs: dict) -> str:
        value = kwargs.get(field)
        if not value and field in self.required:
            raise KeyedEngineError(f'{self.name}: missing credential `{field}`')
        return value

    def client(self, kwargs: dict) -> requests.Session:
        if self.session is None:
            self.session = requests.Session()
        self.session.proxies = kwargs.get('proxies') or {}
        return self.session

    def post(self, url: str, kwargs: dict, **req) -> Union[dict, list]:
        r = self.client(kwargs).post(url, timeout=kwargs.get('timeout') or 20, **req)
        if r.status_code >= 400:
            raise KeyedEngineError(f'{self.name}: HTTP {r.status_code} {r.text[:200]}', KEY_COOLDOWN.get(r.status_code, 0.0))
        return r.json()

    def api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict, list]:
        if not query_text.strip():
            return query_text
        src, tgt = self.code(from_language), self.code(to_language)
        sets = credentials.key_sets(self.name)
        if not sets or all(kwargs.get(f) for f in self.required):  # call kwargs replace the configured keys
            result = self.translate(query_text, src, tgt, {**(sets[0][1] if sets else {}), **kwargs})
        else:
            result, errors = None, []
            for label, fields in KEYS.order(self.name, sets):
                kw = {**{k: v for k, v in fields.items() if k not in META_FIELDS}, **kwargs}
                try:
                    result = self.translate(query_text, src, tgt, kw)
                except KeyedEngineError as e:
                    errors.append(f'[{label}] {e}')
                    if e.cooldown:
                        KEYS.rest(self.name, label, e.cooldown)
                    continue
                KEYS.ok(self.name, label)
                break
            else:
                raise KeyedEngineError(f'{self.name}: every key failed: ' + '; '.join(errors))
        time.sleep(kwargs.get('sleep_seconds', 0))
        return result

    def translate(self, text: str, src: Optional[str], tgt: str, kwargs: dict) -> Union[str, dict, list]:
        raise NotImplementedError


@register('deeplApi', required=('api_key',), optional=('host',))
class DeeplApi(KeyedEngine):
    """DeepL API (Free/Developer keys end with ':fx' and use api-free.deepl.com). HTTP 456 = quota used up."""
    zh_code, zh_hant_code = 'ZH-HANS', 'ZH-HANT'

    def code(self, lang):
        c = super().code(lang)
        return c.upper() if c else c

    def translate(self, text, src, tgt, kwargs):
        key = self.cred('api_key', kwargs)
        host = self.cred('host', kwargs) or ('api-free.deepl.com' if key.endswith(':fx') else 'api.deepl.com')
        body = {'text': [text], 'target_lang': 'EN-US' if tgt == 'EN' else tgt}
        if src:
            body['source_lang'] = src.split('-')[0]  # source_lang takes no variant
        data = self.post(f'https://{host}/v2/translate', kwargs, json=body,
                         headers={'Authorization': f'DeepL-Auth-Key {key}'})
        return data if kwargs.get('is_detail_result') else data['translations'][0]['text']


@register('azure', required=('api_key',), optional=('region', 'endpoint'))
class Azure(KeyedEngine):
    """Azure AI Translator v3 (F0 free tier: 2M chars/month)."""
    zh_code, zh_hant_code = 'zh-Hans', 'zh-Hant'

    def translate(self, text, src, tgt, kwargs):
        headers = {'Ocp-Apim-Subscription-Key': self.cred('api_key', kwargs), 'Content-Type': 'application/json'}
        region = self.cred('region', kwargs)
        if region:
            headers['Ocp-Apim-Subscription-Region'] = region
        endpoint = self.cred('endpoint', kwargs) or 'https://api.cognitive.microsofttranslator.com'
        params = {'api-version': '3.0', 'to': tgt}
        if src:
            params['from'] = src
        data = self.post(endpoint.rstrip('/') + '/translate', kwargs, params=params, json=[{'Text': text}], headers=headers)
        return data if kwargs.get('is_detail_result') else data[0]['translations'][0]['text']


@register('googleCloud', required=('api_key',))
class GoogleCloud(KeyedEngine):
    """Google Cloud Translation Basic v2 with an API key (500k chars/month credit; billing must be enabled)."""
    zh_code, zh_hant_code = 'zh-CN', 'zh-TW'

    def translate(self, text, src, tgt, kwargs):
        body = {'q': [text], 'target': tgt, 'format': 'text'}
        if src:
            body['source'] = src
        data = self.post('https://translation.googleapis.com/language/translate/v2', kwargs,
                         params={'key': self.cred('api_key', kwargs)}, json=body)
        return data if kwargs.get('is_detail_result') else data['data']['translations'][0]['translatedText']


def _salt() -> str:
    import uuid
    return uuid.uuid4().hex[:10]


@register('baiduApi', required=('appid', 'secret_key'))
class BaiduApi(KeyedEngine):
    """Baidu fanyi-api general text translation. Standard tier (no verification): 50k chars/month, 1 QPS."""
    zh_code, zh_hant_code, auto_code = 'zh', 'cht', 'auto'

    @staticmethod
    def sign(appid: str, q: str, salt: str, secret_key: str) -> str:
        import hashlib
        return hashlib.md5((appid + q + salt + secret_key).encode('utf-8')).hexdigest()

    def translate(self, text, src, tgt, kwargs):
        appid, secret_key, salt = self.cred('appid', kwargs), self.cred('secret_key', kwargs), _salt()
        form = {'q': text, 'from': src, 'to': tgt, 'appid': appid, 'salt': salt,
                'sign': self.sign(appid, text, salt, secret_key)}
        data = self.post('https://fanyi-api.baidu.com/api/trans/vip/translate', kwargs, data=form)
        if 'error_code' in data and str(data['error_code']) != '52000':
            raise KeyedEngineError(f"{self.name}: {data['error_code']} {data.get('error_msg', '')}",
                                   {'54004': 3600.0, '58002': 3600.0, '52003': 3600.0, '54003': 60.0}.get(str(data['error_code']), 0.0))
        return data if kwargs.get('is_detail_result') else '\n'.join(x['dst'] for x in data['trans_result'])


@register('youdaoApi', required=('app_key', 'app_secret'))
class YoudaoApi(KeyedEngine):
    """Youdao openapi text translation, signType v3. Free: one-time 50 CNY credit, then billed."""
    zh_code, zh_hant_code, auto_code = 'zh-CHS', 'zh-CHT', 'auto'

    @staticmethod
    def sign(app_key: str, q: str, salt: str, curtime: str, app_secret: str) -> str:
        import hashlib
        short = q if len(q) <= 20 else q[:10] + str(len(q)) + q[-10:]
        return hashlib.sha256((app_key + short + salt + curtime + app_secret).encode('utf-8')).hexdigest()

    def translate(self, text, src, tgt, kwargs):
        app_key, app_secret = self.cred('app_key', kwargs), self.cred('app_secret', kwargs)
        salt, curtime = _salt(), str(int(time.time()))
        form = {'q': text, 'from': src, 'to': tgt, 'appKey': app_key, 'salt': salt, 'signType': 'v3',
                'curtime': curtime, 'sign': self.sign(app_key, text, salt, curtime, app_secret)}
        data = self.post('https://openapi.youdao.com/api', kwargs, data=form)
        if str(data.get('errorCode')) != '0':
            raise KeyedEngineError(f"{self.name}: errorCode {data.get('errorCode')}",
                                   {'401': 3600.0, '108': 3600.0, '411': 60.0}.get(str(data.get('errorCode')), 0.0))
        return data if kwargs.get('is_detail_result') else '\n'.join(data['translation'])


@register('caiyunApi', required=('token',))
class CaiyunApi(KeyedEngine):
    """Caiyun (LingoCloud) translator API. Free: one-time 1M chars valid one month, then billed."""
    zh_code, zh_hant_code, auto_code = 'zh', 'zh-Hant', 'auto'

    def translate(self, text, src, tgt, kwargs):
        body = {'source': [text], 'trans_type': f'{src}2{tgt}', 'request_id': _salt(), 'detect': src == 'auto'}
        data = self.post('https://api.interpreter.caiyunai.com/v1/translator', kwargs, json=body,
                         headers={'X-Authorization': 'token ' + self.cred('token', kwargs)})
        if 'target' not in data:
            raise KeyedEngineError(f'{self.name}: {str(data)[:200]}')
        return data if kwargs.get('is_detail_result') else data['target'][0]


@register('niutransApi', required=('api_key',))
class NiutransApi(KeyedEngine):
    """
    NiuTrans open API (200k chars/day free per its homepage). Request fields follow community wrappers;
    the official doc page is an SPA we could not read, so verify with a real key.
    """
    zh_code, zh_hant_code, auto_code = 'zh', 'cht', 'auto'

    def translate(self, text, src, tgt, kwargs):
        form = {'apikey': self.cred('api_key', kwargs), 'from': src, 'to': tgt, 'src_text': text}
        data = self.post('https://api.niutrans.com/NiuTransServer/translation', kwargs, data=form)
        if 'tgt_text' not in data:
            raise KeyedEngineError(f"{self.name}: {data.get('error_code')} {data.get('error_msg', '')}")
        return data if kwargs.get('is_detail_result') else data['tgt_text']


def _pct(s: str) -> str:
    import urllib.parse
    return urllib.parse.quote(str(s), safe='~')


def aliyun_rpc_sign(secret: str, method: str, params: dict) -> str:
    """Alibaba Cloud RPC signature V1.0 (HMAC-SHA1)."""
    import base64, hashlib, hmac
    canon = '&'.join(f'{_pct(k)}={_pct(params[k])}' for k in sorted(params))
    to_sign = f'{method}&{_pct("/")}&{_pct(canon)}'
    return base64.b64encode(hmac.new((secret + '&').encode(), to_sign.encode(), hashlib.sha1).digest()).decode()


def volc_sign(secret: str, method: str, query: dict, headers: dict, body: str, xdate: str, region: str, service: str) -> str:
    """Volcengine HMAC-SHA256 request signature; `headers` are the signed headers (lowercase names)."""
    import hashlib, hmac
    names = sorted(headers)
    canonical = '\n'.join([method, '/', '&'.join(f'{_pct(k)}={_pct(query[k])}' for k in sorted(query)),
                           ''.join(f'{n}:{headers[n]}\n' for n in names), ';'.join(names),
                           hashlib.sha256(body.encode()).hexdigest()])
    scope = f'{xdate[:8]}/{region}/{service}/request'
    to_sign = '\n'.join(['HMAC-SHA256', xdate, scope, hashlib.sha256(canonical.encode()).hexdigest()])
    key = secret.encode()
    for part in (xdate[:8], region, service, 'request'):
        key = hmac.new(key, part.encode(), hashlib.sha256).digest()
    return hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()


@register('aliyunApi', required=('access_key_id', 'access_key_secret'), optional=('endpoint',))
class AliyunApi(KeyedEngine):
    """
    Alibaba Cloud Machine Translation TranslateGeneral (1M chars/month free on both CN and intl sites).
    Overage is billed from account balance, not blocked. Use a RAM key limited to alimt:TranslateGeneral.
    """
    zh_code, zh_hant_code, auto_code = 'zh', 'zh-tw', 'auto'

    def translate(self, text, src, tgt, kwargs):
        import datetime, uuid
        params = {
            'Action': 'TranslateGeneral', 'Version': '2018-10-12', 'Format': 'JSON',
            'AccessKeyId': self.cred('access_key_id', kwargs), 'SignatureMethod': 'HMAC-SHA1',
            'SignatureVersion': '1.0', 'SignatureNonce': uuid.uuid4().hex,
            'Timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'FormatType': 'text', 'Scene': 'general', 'SourceLanguage': src, 'TargetLanguage': tgt, 'SourceText': text,
        }
        params['Signature'] = aliyun_rpc_sign(self.cred('access_key_secret', kwargs), 'POST', params)
        endpoint = self.cred('endpoint', kwargs) or 'mt.aliyuncs.com'
        data = self.post(f'https://{endpoint}/', kwargs, data=params)
        if str(data.get('Code')) != '200':
            raise KeyedEngineError(f"{self.name}: {data.get('Code')} {data.get('Message', '')}")
        return data if kwargs.get('is_detail_result') else data['Data']['Translated']


@register('volcEngineApi', required=('access_key_id', 'secret_access_key'), optional=('region',))
class VolcEngineApi(KeyedEngine):
    """Volcengine machine translation TranslateText (official API; free quota and overseas signup unverified)."""
    zh_code, zh_hant_code, auto_code = 'zh', 'zh-Hant', None

    def translate(self, text, src, tgt, kwargs):
        import datetime, hashlib, json
        host, region, service = 'translate.volcengineapi.com', self.cred('region', kwargs) or 'cn-north-1', 'translate'
        query = {'Action': 'TranslateText', 'Version': '2020-06-01'}
        payload = {'TargetLanguage': tgt, 'TextList': [text]}
        if src:
            payload['SourceLanguage'] = src
        body = json.dumps(payload, ensure_ascii=False)
        xdate = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        signed = {'content-type': 'application/json', 'host': host, 'x-content-sha256': hashlib.sha256(body.encode()).hexdigest(),
                  'x-date': xdate}
        ak = self.cred('access_key_id', kwargs)
        sig = volc_sign(self.cred('secret_access_key', kwargs), 'POST', query, signed, body, xdate, region, service)
        headers = {'Content-Type': signed['content-type'], 'X-Date': xdate, 'X-Content-Sha256': signed['x-content-sha256'],
                   'Authorization': f'HMAC-SHA256 Credential={ak}/{xdate[:8]}/{region}/{service}/request, '
                                    f'SignedHeaders={";".join(sorted(signed))}, Signature={sig}'}
        data = self.post(f'https://{host}/', kwargs, params=query, data=body.encode(), headers=headers)
        err = (data.get('ResponseMetadata') or {}).get('Error')
        if err:
            raise KeyedEngineError(f"{self.name}: {err.get('Code')} {err.get('Message', '')}")
        return data if kwargs.get('is_detail_result') else data['TranslationList'][0]['Translation']
