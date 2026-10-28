# coding=utf-8
"""Offline tests for engine fallback and `preserve`. Fake engines replace the network ones."""

import asyncio
import os
import unittest
from unittest import mock

# `import translators` detects the server region over the network unless this is set.
os.environ.setdefault('translators_default_region', 'EN')

from translators import preserve as pv  # noqa: E402
from translators import server as srv  # noqa: E402
from translators import server_async as srv_async  # noqa: E402

TranslatorError = srv.TranslatorError
PATTERNS = [r'`[^`]*`', r'\bv\d+\.\d+\b']
TEXT = 'Run `make test` before you push v1.2.'


def fake_raise(query_text, **kwargs):
    raise RuntimeError('boom')


def fake_drop(query_text, **kwargs):
    return 'Drop: ' + query_text.replace('QX1Z', '')


def fake_ok(query_text, **kwargs):
    return 'T:' + query_text


def fake_empty(query_text, **kwargs):
    return '   '


class TestPreserveHelpers(unittest.TestCase):
    def test_round_trip(self):
        masked, spans = pv.mask(TEXT, PATTERNS)
        self.assertEqual(spans, ['`make test`', 'v1.2'])
        self.assertNotIn('`', masked)
        self.assertIn('QX1Z', masked)
        self.assertEqual(pv.restore(masked, spans), TEXT[:-1] + '.')

    def test_round_trip_exact_when_no_trailing_punct(self):
        text = 'Use `ls` now'
        masked, spans = pv.mask(text, PATTERNS)
        self.assertEqual(pv.restore(masked, spans), text)

    def test_restore_tolerates_case_and_inner_spaces(self):
        _, spans = pv.mask('see `x` here', PATTERNS)
        self.assertEqual(pv.restore('voir q x 1 z ici', spans), 'voir `x` ici')
        self.assertEqual(pv.restore('voir qx1z, ici', spans), 'voir `x`, ici')

    def test_tidy_punctuation_and_parens(self):
        _, spans = pv.mask('(`x`).', PATTERNS)
        self.assertEqual(pv.restore('( QX1Z ).', spans), '(`x`).')

    def test_no_patterns_or_no_match(self):
        self.assertEqual(pv.mask(TEXT, None), (TEXT, []))
        self.assertEqual(pv.mask('plain', PATTERNS), ('plain', []))
        self.assertEqual(pv.restore('anything', []), 'anything')

    def test_token_loss_detected(self):
        _, spans = pv.mask(TEXT, PATTERNS)
        with self.assertRaises(pv.PreserveError):
            pv.restore('only QX1Z here', spans)

    def test_token_duplication_detected(self):
        _, spans = pv.mask('a `x` b', PATTERNS)
        with self.assertRaises(pv.PreserveError):
            pv.restore('QX1Z and QX1Z', spans)

    def test_replacement_text_with_backslash_is_literal(self):
        _, spans = pv.mask(r'a \1 b', [r'\\\d'])
        self.assertEqual(pv.restore('x QX1Z y', spans), r'x \1 y')

    def test_normalize_engines(self):
        self.assertEqual(pv.normalize_engines('google, bing'), ['google', 'bing'])
        self.assertEqual(pv.normalize_engines(('a', 'b')), ['a', 'b'])
        self.assertEqual(pv.normalize_engines('google'), ['google'])


class _ServerCase(unittest.TestCase):
    module = srv

    def setUp(self):
        self.tss = self.module.tss
        pv.HEALTH.reset()
        fakes = {'fake_raise': fake_raise, 'fake_drop': fake_drop, 'fake_ok': fake_ok, 'fake_empty': fake_empty}
        self.fakes = fakes
        patch_dict = mock.patch.dict(self.tss.translators_dict, self._wrap(fakes))
        patch_pool = mock.patch.object(self.tss, 'translators_pool', list(self.tss.translators_pool) + list(fakes))
        patch_dict.start()
        patch_pool.start()
        self.addCleanup(patch_dict.stop)
        self.addCleanup(patch_pool.stop)

    def _wrap(self, fakes):
        return fakes

    def call(self, *args, **kwargs):
        return self.tss.translate_text(*args, **kwargs)


class TestFallbackSync(_ServerCase):
    def test_single_string_backward_compatible(self):
        self.assertEqual(self.call('hi', translator='fake_ok'), 'T:hi')
        self.assertEqual(self.call('hi', translator='fake_ok', if_return_engine=True), ('T:hi', 'fake_ok'))

    def test_single_string_unknown_raises_translator_error(self):
        with self.assertRaises(TranslatorError):
            self.call('hi', translator='no_such_engine')

    def test_single_string_engine_exception_propagates_unchanged(self):
        with self.assertRaises(RuntimeError):
            self.call('hi', translator='fake_raise')

    def test_fallback_skips_raise_unknown_empty_and_token_drop(self):
        text, engine = self.call(
            TEXT, translator=['no_such_engine', 'fake_raise', 'fake_empty', 'fake_drop', 'fake_ok'],
            preserve=PATTERNS, if_return_engine=True)
        self.assertEqual(engine, 'fake_ok')
        self.assertEqual(text, 'T:Run `make test` before you push v1.2.')

    def test_comma_string_and_tuple(self):
        self.assertEqual(self.call('hi', translator='fake_raise,fake_ok', if_return_engine=True), ('T:hi', 'fake_ok'))
        self.assertEqual(self.call('hi', translator=('fake_raise', 'fake_ok')), 'T:hi')

    def test_preserve_with_single_engine_failure_is_translator_error(self):
        with self.assertRaises(TranslatorError):
            self.call(TEXT, translator='fake_drop', preserve=PATTERNS)

    def test_all_fail_message_lists_each_engine_and_reason(self):
        with self.assertRaises(TranslatorError) as cm:
            self.call(TEXT, translator=['fake_raise', 'fake_drop', 'fake_empty', 'no_such_engine'], preserve=PATTERNS)
        msg = str(cm.exception)
        for part in ('fake_raise -> RuntimeError: boom', 'fake_drop -> PreserveError',
                     'fake_empty -> TranslatorError: empty result', 'no_such_engine -> not in translators_pool'):
            self.assertIn(part, msg)

    def test_detail_result_returned_unchanged(self):
        detail = {'raw': 1}
        with mock.patch.dict(self.tss.translators_dict, {'fake_detail': lambda query_text, **kw: detail}), \
                mock.patch.object(self.tss, 'translators_pool', self.tss.translators_pool + ['fake_detail']):
            result = self.call('hi', translator=['fake_raise', 'fake_detail'], is_detail_result=True)
        self.assertIs(result, detail)

    def test_preserve_with_detail_result_raises(self):
        with self.assertRaises(TranslatorError):
            self.call(TEXT, translator=['fake_ok'], preserve=PATTERNS, is_detail_result=True)

    def test_empty_list_raises(self):
        with self.assertRaises(TranslatorError):
            self.call('hi', translator=[])


class TestFallbackAsync(unittest.TestCase):
    def setUp(self):
        pv.HEALTH.reset()
        self.tss = srv_async.tss

        async def a_raise(query_text, **kw):
            raise RuntimeError('boom')

        async def a_drop(query_text, **kw):
            return query_text.replace('QX1Z', '')

        async def a_ok(query_text, **kw):
            return 'T:' + query_text

        fakes = {'a_raise': a_raise, 'a_drop': a_drop, 'a_ok': a_ok}
        p1 = mock.patch.dict(self.tss.translators_dict, fakes)
        p2 = mock.patch.object(self.tss, 'translators_pool', list(self.tss.translators_pool) + list(fakes))
        p1.start()
        p2.start()
        self.addCleanup(p1.stop)
        self.addCleanup(p2.stop)

    def run_async(self, *args, **kwargs):
        return asyncio.run(self.tss.translate_text(*args, if_close_session=False, **kwargs))

    def test_fallback(self):
        text, engine = self.run_async(
            TEXT, translator=['a_raise', 'a_drop', 'a_ok'], preserve=PATTERNS, if_return_engine=True)
        self.assertEqual((text, engine), ('T:Run `make test` before you push v1.2.', 'a_ok'))

    def test_single_string_and_unknown(self):
        self.assertEqual(self.run_async('hi', translator='a_ok'), 'T:hi')
        with self.assertRaises(srv_async.TranslatorError):
            self.run_async('hi', translator='no_such_engine')

    def test_all_fail_message(self):
        with self.assertRaises(srv_async.TranslatorError) as cm:
            self.run_async(TEXT, translator='a_raise,a_drop', preserve=PATTERNS)
        self.assertIn('a_raise -> RuntimeError: boom', str(cm.exception))
        self.assertIn('a_drop -> PreserveError', str(cm.exception))



class TestPresetAndHealth(_ServerCase):
    def test_code_preset_protects_common_spans(self):
        text = ('Run `make test`, edit src/app/main.py and build/out.txt, see #42, '
                'pass --dry-run to sellPriceTax via MAX_RETRY on v6.0.4 at https://x.io/a?b=1 now.')
        masked, spans = pv.mask(text, 'code')
        self.assertEqual(spans, ['`make test`', 'src/app/main.py', 'build/out.txt', '#42', '--dry-run',
                                 'sellPriceTax', 'MAX_RETRY', 'v6.0.4', 'https://x.io/a?b=1'])
        self.assertEqual(pv.restore(masked, spans), text)

    def test_code_preset_stops_at_cjk(self):
        text = '\u68c0\u67e5build/out.txt\u4e2d\u7684sellPriceTax\u548c`ls`'
        _, spans = pv.mask(text, 'code')
        self.assertEqual(spans, ['build/out.txt', 'sellPriceTax', '`ls`'])

    def test_preset_mixes_with_regex(self):
        self.assertEqual(pv.expand_patterns(['code', r'\bRealm\b'])[-1], r'\bRealm\b')
        self.assertEqual(pv.expand_patterns(None), [])

    def test_failing_engine_moves_to_back_after_threshold(self):
        calls = []
        def flaky(query_text, **kw):
            calls.append('fake_raise')
            raise RuntimeError('down')
        self.tss.translators_dict['fake_raise'] = flaky
        for _ in range(3):
            self.assertEqual(self.call(TEXT, translator=['fake_raise', 'fake_ok']), 'T:' + TEXT)
        self.assertEqual(len(calls), 3)
        self.assertTrue(pv.HEALTH.is_cooling('fake_raise'))
        result, engine = self.call(TEXT, translator=['fake_raise', 'fake_ok'], if_return_engine=True)
        self.assertEqual((engine, len(calls)), ('fake_ok', 3))  # skipped while cooling

    def test_cooling_engine_still_tried_when_alone(self):
        for _ in range(3):
            pv.HEALTH.fail('fake_ok')
        self.assertEqual(self.call(TEXT, translator=['fake_ok', 'fake_raise']), 'T:' + TEXT)
        self.assertFalse(pv.HEALTH.is_cooling('fake_ok'))

    def test_preserve_error_does_not_count_as_engine_failure(self):
        for _ in range(4):
            self.call(TEXT, translator=['fake_drop', 'fake_ok'], preserve=PATTERNS)
        self.assertFalse(pv.HEALTH.is_cooling('fake_drop'))



class TestRetiredAndAliases(_ServerCase):
    def test_retired_engines_left_out_of_pool(self):
        from translators import retired
        for name in list(retired.RETIRED_TRANSLATORS) + list(retired.TRANSLATOR_ALIASES):
            self.assertNotIn(name, srv.tss.translators_pool)
            self.assertNotIn(name, srv_async.tss.translators_pool)

    def test_retired_single_name_raises_with_reason(self):
        with self.assertRaises(TranslatorError) as cm:
            self.call(TEXT, translator='judic')
        self.assertIn('retired', str(cm.exception))

    def test_retired_in_chain_is_skipped(self):
        result, engine = self.call(TEXT, translator=['judic', 'fake_ok'], if_return_engine=True)
        self.assertEqual(engine, 'fake_ok')

    def test_alias_resolves(self):
        with mock.patch('translators.retired.TRANSLATOR_ALIASES', {'old_ok': 'fake_ok'}):
            self.assertEqual(self.call(TEXT, translator='old_ok', if_return_engine=True), ('T:' + TEXT, 'fake_ok'))
            self.assertEqual(self.call(TEXT, translator=['old_ok'], if_return_engine=True)[1], 'fake_ok')


if __name__ == '__main__':
    unittest.main()
