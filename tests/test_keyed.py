# coding=utf-8
"""Offline tests for credentials and keyed engines. HTTP is mocked."""

import asyncio
import os
import stat
import tempfile
import unittest
import warnings
from unittest import mock

os.environ.setdefault('translators_default_region', 'EN')

import translators  # noqa: E402
from translators import credentials, keyed  # noqa: E402
from translators import server as srv  # noqa: E402
from translators import server_async as srv_async  # noqa: E402


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status_code, self.text = payload, status, str(payload)

    def json(self):
        return self.payload


class _CredsCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, 'credentials.toml')
        env = {k: v for k, v in os.environ.items() if not k.startswith('TRANSLATORS_')}
        env['TRANSLATORS_CREDENTIALS'] = self.path
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(translators.refresh_keyed_engines)

    def write(self, text, mode=0o600):
        with open(self.path, 'w') as f:
            f.write(text)
        os.chmod(self.path, mode)


class TestCredentials(_CredsCase):
    def test_file_then_env_override(self):
        self.write('[deeplApi]\napi_key = "file-key:fx"\n\n[azure]\napi_key = "az"\nregion = "australiaeast"\n')
        creds = credentials.load()
        self.assertEqual(creds['deeplApi']['api_key'], 'file-key:fx')
        self.assertEqual(creds['azure']['region'], 'australiaeast')
        os.environ['TRANSLATORS_DEEPLAPI_API_KEY'] = 'env-key'
        self.assertEqual(credentials.load()['deeplApi']['api_key'], 'env-key')
        self.assertEqual(credentials.get('deeplApi', 'api_key', {'api_key': 'call-key'}), 'call-key')

    def test_is_configured_needs_all_required(self):
        self.write('[azure]\nregion = "x"\n')
        self.assertFalse(credentials.is_configured('azure'))
        self.assertFalse(credentials.is_configured('googleCloud'))
        os.environ['TRANSLATORS_GOOGLECLOUD_API_KEY'] = 'g'
        self.assertTrue(credentials.is_configured('googleCloud'))

    def test_world_readable_file_warns(self):
        if os.name != 'posix':
            self.skipTest('posix only')
        self.write('[azure]\napi_key = "az"\n', mode=0o644)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            credentials.load()
        self.assertTrue(any('chmod 600' in str(x.message) for x in w))


class TestKeychain(_CredsCase):
    def test_keychain_placeholder_is_resolved(self):
        self.write('[deeplApi]\napi_key = "@keychain"\n')
        done = mock.Mock(returncode=0, stdout='secret:fx\n')
        with mock.patch.object(credentials.sys, 'platform', 'darwin'), \
                mock.patch.object(credentials.os.path, 'exists', return_value=True), \
                mock.patch.object(credentials.subprocess, 'run', return_value=done) as run:
            creds = credentials.load()
        self.assertEqual(creds['deeplApi']['api_key'], 'secret:fx')
        self.assertEqual(run.call_args.args[0][-5:], ['-s', 'translators', '-a', 'deeplApi.api_key', '-w'])
        self.assertEqual(credentials.get('deeplApi', 'api_key'), 'secret:fx')  # served from cache

    def test_other_os_uses_keyring_package(self):
        self.write('[azure]\napi_key = "@keyring"\n')
        fake = mock.Mock()
        fake.get_password.return_value = 'az-secret'
        with mock.patch.object(credentials.sys, 'platform', 'win32'), mock.patch.dict('sys.modules', {'keyring': fake}):
            creds = credentials.load()
        self.assertEqual(creds['azure']['api_key'], 'az-secret')
        fake.get_password.assert_called_once_with('translators', 'azure.api_key')

    def test_other_os_without_keyring_package_warns(self):
        self.write('[azure]\napi_key = "@keyring"\n')
        with mock.patch.object(credentials.sys, 'platform', 'linux'), mock.patch.dict('sys.modules', {'keyring': None}), \
                warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            creds = credentials.load()
        self.assertFalse(credentials.is_configured('azure', creds))
        self.assertTrue(any('pip install keyring' in str(x.message) for x in w))

    def test_missing_keychain_item_leaves_engine_unconfigured(self):
        self.write('[deeplApi]\napi_key = "@keychain"\n')
        with mock.patch.object(credentials.sys, 'platform', 'darwin'), \
                mock.patch.object(credentials.os.path, 'exists', return_value=True), \
                mock.patch.object(credentials.subprocess, 'run', return_value=mock.Mock(returncode=44, stdout='')), \
                warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            creds = credentials.load()
        self.assertFalse(credentials.is_configured('deeplApi', creds))
        self.assertTrue(any('No credential-store item' in str(x.message) for x in w))


class TestPool(_CredsCase):
    def test_configured_engine_joins_both_pools(self):
        self.assertNotIn('deeplApi', translators.translators_pool)
        self.write('[deeplApi]\napi_key = "k:fx"\n')
        self.assertEqual(translators.refresh_keyed_engines(), ['deeplApi'])
        self.assertIn('deeplApi', translators.translators_pool)
        self.assertIn('deeplApi', srv_async.tss.translators_pool)
        os.remove(self.path)
        translators.refresh_keyed_engines()
        self.assertNotIn('deeplApi', translators.translators_pool)
        self.assertNotIn('deeplApi', srv_async.tss.translators_pool)


class _EngineCase(_CredsCase):
    def call(self, engine, payload, **kw):
        with mock.patch('requests.Session.post', return_value=FakeResponse(payload)) as post:
            out = keyed.KEYED_CLASSES[engine]().api('Hello', kw.pop('src', 'en'), kw.pop('tgt', 'zh'), **kw)
        return out, post.call_args


class TestEngines(_EngineCase):
    def test_deepl_free_host_and_codes(self):
        out, call = self.call('deeplApi', {'translations': [{'text': '你好'}]}, api_key='k:fx', src='auto', tgt='zh-TW')
        self.assertEqual(out, '你好')
        self.assertEqual(call.args[0], 'https://api-free.deepl.com/v2/translate')
        self.assertEqual(call.kwargs['json'], {'text': ['Hello'], 'target_lang': 'ZH-HANT'})
        self.assertEqual(call.kwargs['headers']['Authorization'], 'DeepL-Auth-Key k:fx')
        _, call = self.call('deeplApi', {'translations': [{'text': 'x'}]}, api_key='pro', src='zh', tgt='en')
        self.assertEqual(call.args[0], 'https://api.deepl.com/v2/translate')
        self.assertEqual(call.kwargs['json'], {'text': ['Hello'], 'target_lang': 'EN-US', 'source_lang': 'ZH'})

    def test_azure_region_and_codes(self):
        out, call = self.call('azure', [{'translations': [{'text': '你好', 'to': 'zh-Hans'}]}], api_key='a', region='eastus')
        self.assertEqual(out, '你好')
        self.assertEqual(call.kwargs['params'], {'api-version': '3.0', 'to': 'zh-Hans', 'from': 'en'})
        self.assertEqual(call.kwargs['headers']['Ocp-Apim-Subscription-Region'], 'eastus')
        self.assertEqual(call.kwargs['json'], [{'Text': 'Hello'}])

    def test_google_cloud_key_param(self):
        out, call = self.call('googleCloud', {'data': {'translations': [{'translatedText': '你好'}]}}, api_key='g', src='auto')
        self.assertEqual(out, '你好')
        self.assertEqual(call.kwargs['params'], {'key': 'g'})
        self.assertEqual(call.kwargs['json'], {'q': ['Hello'], 'target': 'zh-CN', 'format': 'text'})

    def test_http_error_raises_and_chain_falls_back(self):
        self.write('[azure]\napi_key = "a"\n')
        translators.refresh_keyed_engines()
        with mock.patch('requests.Session.post', return_value=FakeResponse({'error': 'quota'}, 403)):
            with self.assertRaises(keyed.KeyedEngineError):
                keyed.Azure().api('Hello', 'en', 'zh', api_key='a')
            fake = mock.Mock(return_value='T:Hello')
            with mock.patch.dict(srv.tss.translators_dict, {'bing': fake}):
                out = srv.tss.translate_text('Hello', translator=['azure', 'bing'], to_language='zh', if_return_engine=True)
        self.assertEqual(out, ('T:Hello', 'bing'))

    def test_async_runs_in_executor(self):
        self.write('[googleCloud]\napi_key = "g"\n')
        translators.refresh_keyed_engines()
        payload = {'data': {'translations': [{'translatedText': '你好'}]}}
        with mock.patch('requests.Session.post', return_value=FakeResponse(payload)):
            out = asyncio.run(srv_async.tss.translate_text('Hello', translator='googleCloud', from_language='en',
                                                           to_language='zh', if_close_session=False))
        self.assertEqual(out, '你好')



class TestSigning(unittest.TestCase):
    def test_baidu_official_vector(self):
        self.assertEqual(keyed.BaiduApi.sign('2015063000000001', 'apple', '65478', '1234567890'),
                         'a1a7461d92e5194c5cae3182b5b24de1')

    def test_aliyun_official_vector(self):
        params = {'AccessKeyId': 'testid', 'Action': 'DescribeDedicatedHosts', 'Format': 'JSON',
                  'RegionId': 'cn-beijing', 'SignatureMethod': 'HMAC-SHA1',
                  'SignatureNonce': 'edb2b34af0af9a6d14deaf7c1a5315eb', 'SignatureVersion': '1.0',
                  'Timestamp': '2023-03-13T08:34:30Z', 'Version': '2014-05-26'}
        self.assertEqual(keyed.aliyun_rpc_sign('testsecret', 'GET', params), '9NaGiOspFP5UPcwX8Iwt2YJXXuk=')

    def test_volcengine_official_vector(self):
        sig = keyed.volc_sign('WkRZeE1EQmxPVGhsWWpWak5HVmtNbUUxTXpZeU9UVXlOMlE1TmpZeVlqTQ==', 'POST',
                              {'Action': 'ListBill', 'Version': '2022-01-01'},
                              {'host': 'billing.volcengineapi.com', 'x-date': '20250329T180937Z'},
                              '{"Limit":10,"BillPeriod":"2023-08"}', '20250329T180937Z', 'cn-beijing', 'billing')
        self.assertEqual(sig, '5e8480ceea12d0000a23c054151c50dd02c1a7dec835004057d19f13d53a7658')

    def test_youdao_truncates_long_input(self):
        import hashlib
        q = 'abcdefghij' + 'x' * 30 + '0123456789'
        want = hashlib.sha256(('K' + 'abcdefghij500123456789' + 'S' + '1' + 'P').encode()).hexdigest()
        self.assertEqual(keyed.YoudaoApi.sign('K', q, 'S', '1', 'P'), want)
        self.assertEqual(keyed.YoudaoApi.sign('APPID', 'good', 'SALT1', '1700000000', 'SECRET'),
                         'a24b45a10394b61eba258c7536d592395680251f26c7c6a9f2c3b4b5a572d5c3')


class TestCnEngines(_EngineCase):
    def test_baidu_request_and_error(self):
        out, call = self.call('baiduApi', {'trans_result': [{'dst': '\u4f60\u597d'}]}, appid='a', secret_key='s', tgt='zh-TW')
        self.assertEqual(out, '\u4f60\u597d')
        form = call.kwargs['data']
        self.assertEqual((form['from'], form['to']), ('en', 'cht'))
        self.assertEqual(form['sign'], keyed.BaiduApi.sign('a', 'Hello', form['salt'], 's'))
        with self.assertRaises(keyed.KeyedEngineError):
            self.call('baiduApi', {'error_code': '54003', 'error_msg': 'limit'}, appid='a', secret_key='s')

    def test_youdao_caiyun_niutrans_shapes(self):
        out, call = self.call('youdaoApi', {'errorCode': '0', 'translation': ['Y']}, app_key='k', app_secret='p')
        self.assertEqual((out, call.kwargs['data']['to'], call.kwargs['data']['signType']), ('Y', 'zh-CHS', 'v3'))
        out, call = self.call('caiyunApi', {'target': ['C']}, token='t', src='auto', tgt='zh-TW')
        self.assertEqual((out, call.kwargs['json']['trans_type'], call.kwargs['json']['detect']), ('C', 'auto2zh-Hant', True))
        self.assertEqual(call.kwargs['headers']['X-Authorization'], 'token t')
        out, call = self.call('niutransApi', {'tgt_text': 'N'}, api_key='n')
        self.assertEqual((out, call.kwargs['data']['apikey']), ('N', 'n'))

    def test_aliyun_and_volcengine_requests(self):
        out, call = self.call('aliyunApi', {'Code': '200', 'Data': {'Translated': 'A'}},
                              access_key_id='id', access_key_secret='sec', src='auto', tgt='zh-TW')
        form = dict(call.kwargs['data'])
        sig = form.pop('Signature')
        self.assertEqual((out, form['SourceLanguage'], form['TargetLanguage']), ('A', 'auto', 'zh-tw'))
        self.assertEqual(sig, keyed.aliyun_rpc_sign('sec', 'POST', form))
        out, call = self.call('volcEngineApi', {'TranslationList': [{'Translation': 'V'}]},
                              access_key_id='AK', secret_access_key='SK', src='auto')
        self.assertEqual(out, 'V')
        self.assertEqual(call.kwargs['params'], {'Action': 'TranslateText', 'Version': '2020-06-01'})
        self.assertNotIn(b'SourceLanguage', call.kwargs['data'])
        self.assertTrue(call.kwargs['headers']['Authorization'].startswith('HMAC-SHA256 Credential=AK/'))
        with self.assertRaises(keyed.KeyedEngineError):
            self.call('volcEngineApi', {'ResponseMetadata': {'Error': {'Code': 'x'}}},
                      access_key_id='AK', secret_access_key='SK')


if __name__ == '__main__':
    unittest.main()
