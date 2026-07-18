import inspect
import subprocess
import sys
import unittest

import aiohttp
import httpx

import translators as ts
from translators.server_async import Reverso, TranslatorError, Tse, _resolve_http_client


class PackageLoadingTest(unittest.TestCase):
    def test_sync_import_does_not_load_async_module(self):
        result = subprocess.run(
            [
                sys.executable,
                '-c',
                "import sys; import translators; assert 'translators.server_async' not in sys.modules",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_async_compatibility_names_are_coroutine_functions(self):
        self.assertTrue(inspect.iscoroutinefunction(ts.translate_text_with_async))
        self.assertTrue(inspect.iscoroutinefunction(ts.translate_html_with_async))
        self.assertTrue(inspect.iscoroutinefunction(ts.preaccelerate_and_speedtest_with_async))
        self.assertTrue(inspect.iscoroutinefunction(ts.close_with_async))


class AsyncClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_session_type_selects_http_client(self):
        aiohttp_session = aiohttp.ClientSession()
        httpx_session = httpx.AsyncClient()
        try:
            self.assertEqual(_resolve_http_client(None, None), 'aiohttp')
            self.assertEqual(_resolve_http_client(None, 'httpx'), 'httpx')
            self.assertEqual(_resolve_http_client(aiohttp_session, None), 'aiohttp')
            self.assertEqual(_resolve_http_client(httpx_session, None), 'httpx')
            with self.assertRaisesRegex(TranslatorError, 'does not match'):
                _resolve_http_client(aiohttp_session, 'httpx')
            with self.assertRaisesRegex(TranslatorError, 'does not match'):
                _resolve_http_client(httpx_session, 'aiohttp')
        finally:
            await aiohttp_session.close()
            await httpx_session.aclose()

    async def test_aiohttp_proxy_support_is_checked_before_session_creation(self):
        proxy_url = 'http://127.0.0.1:9'
        if 'proxy' not in inspect.signature(aiohttp.ClientSession).parameters:
            with self.assertRaisesRegex(TranslatorError, 'use httpx'):
                Tse.get_client_session('aiohttp', {'https': proxy_url})
            return

        session = Tse.get_client_session('aiohttp', {'https': proxy_url})
        await session.close()

    async def test_session_factories_close_cleanly(self):
        aiohttp_session = Tse.get_client_session('aiohttp')
        httpx_session = Tse.get_client_session('httpx', {'https': 'http://127.0.0.1:9'})
        await aiohttp_session.close()
        await httpx_session.aclose()

    async def test_reverso_rejects_switching_a_live_cached_session(self):
        sessions = (
            (httpx.AsyncClient(), 'aiohttp'),
            (aiohttp.ClientSession(), 'httpx'),
        )
        for session, requested_http_client in sessions:
            reverso = Reverso()
            reverso.session = session
            try:
                with self.assertRaisesRegex(TranslatorError, 'does not match'):
                    await reverso.reverso_api(
                        'hello',
                        http_client=requested_http_client,
                        if_print_warning=False,
                    )
            finally:
                if isinstance(session, aiohttp.ClientSession):
                    await session.close()
                else:
                    await session.aclose()


if __name__ == '__main__':
    unittest.main()
