# coding=utf-8
# author=UlionTse

"""
Pure helpers (no network) for engine fallback and do-not-translate spans.

mask() swaps every span matched by the `preserve` regexes for a placeholder
token ` QX{n}Z `; restore() puts the original spans back and verifies that
the engine kept every token exactly once.
"""

import re
import time
import threading
from typing import Dict, Iterable, List, Optional, Tuple, Union

__all__ = ('PreserveError', 'PRESETS', 'expand_patterns', 'EngineHealth', 'HEALTH',
           'normalize_engines', 'mask', 'restore')

_EXT = (r'py|js|ts|tsx|jsx|go|rs|php|rb|java|kt|swift|c|h|cpp|cs|sh|md|txt|log|json|ya?ml|toml'
        r'|ini|cfg|xml|html|css|sql|csv|lock|patch|diff')

# Named pattern sets usable in `preserve`; earlier patterns win at the same position.
PRESETS: Dict[str, List[str]] = {
    'code': [
        r'https?://[^\s<>"\'`]+',                 # URLs
        r'`[^`\n]+`',                             # inline code spans
        r'(?:\.{0,2}/)?(?:[\w.-]+/)+[\w.-]*',     # paths with a slash
        r'\b[\w.-]*\w\.(?:' + _EXT + r')\b',      # file names
        r'(?<![\w`])\.(?:' + _EXT + r')\b',       # bare extensions (.txt)
        r'(?<![\w&])#\d+\b',                      # issue / MR refs
        r'(?<![\w-])--?[A-Za-z][\w-]*',           # CLI flags
        r'\b[a-z]+[A-Z]\w*\b',                    # camelCase
        r'\b[A-Z][a-z]+[A-Z]\w*\b',               # PascalCase with an inner capital
        r'\b[A-Za-z]\w*_\w+\b',                   # snake_case / CONST_CASE
        r'\bv?\d+(?:\.\d+)+\b',                   # versions
    ],
}


def expand_patterns(preserve: Union[None, str, Iterable[str]]) -> List[str]:
    """
    :param preserve: None, a preset name ('code'), or an iterable mixing preset names and regex patterns.
    :return: flat list of regex patterns.
    """
    if not preserve:
        return []
    if isinstance(preserve, str):
        preserve = [preserve]
    out = []
    for p in preserve:
        if p in PRESETS:
            out.extend(PRESETS[p])
        elif p:
            out.append(p)
    return out


class EngineHealth:
    """
    Process-wide record of engine failures. An engine that failed `threshold` times in a row is
    tried last for `cooldown` seconds, so a fallback chain stops waiting on a dead engine first.
    """

    def __init__(self, threshold: int = 3, cooldown: float = 300.0):
        self.threshold, self.cooldown = threshold, cooldown
        self._fails: Dict[str, int] = {}
        self._since: Dict[str, float] = {}
        self._lock = threading.Lock()

    def ok(self, engine: str) -> None:
        with self._lock:
            self._fails.pop(engine, None)
            self._since.pop(engine, None)

    def fail(self, engine: str) -> None:
        with self._lock:
            self._fails[engine] = self._fails.get(engine, 0) + 1
            if self._fails[engine] >= self.threshold:
                self._since.setdefault(engine, time.monotonic())

    def is_cooling(self, engine: str) -> bool:
        with self._lock:
            since = self._since.get(engine)
            if since is None:
                return False
            if time.monotonic() - since >= self.cooldown:
                self._since.pop(engine, None)
                self._fails[engine] = self.threshold - 1  # one more failure re-trips it
                return False
            return True

    def order(self, engines: List[str]) -> List[str]:
        """Healthy engines first (keeping caller order), cooling ones last; none is dropped."""
        cooling = [e for e in engines if self.is_cooling(e)]
        return [e for e in engines if e not in cooling] + cooling

    def reset(self) -> None:
        with self._lock:
            self._fails.clear()
            self._since.clear()


HEALTH = EngineHealth()

_NO_SPACE_BEFORE = ",.;:!?)\uff0c\u3002\uff1b\uff1a\uff01\uff1f\uff09\u3001"
_NO_SPACE_AFTER = "(\uff08"


class PreserveError(ValueError):
    """A placeholder token was lost or duplicated by the engine."""


def normalize_engines(translator: Union[str, Iterable[str]]) -> List[str]:
    """
    :param translator: str (a comma-separated string is allowed) or an iterable of engine names.
    :return: list of engine names, in order, blanks dropped.
    """
    if isinstance(translator, str):
        translator = translator.split(',')
    return [str(t).strip() for t in translator if str(t).strip()]


def _token(n: int) -> str:
    return f' QX{n}Z '


def _token_pattern(n: int) -> 're.Pattern':
    return re.compile(r'(\s*)q\s*x\s*{}\s*z(\s*)'.format(n), re.IGNORECASE)


def mask(text: str, patterns: Optional[Iterable[str]]) -> Tuple[str, List[str]]:
    """
    Replace every match of `patterns` with a placeholder token.
    The patterns are joined into one alternation regex, so scanning is left to right
    and, at one position, the earlier pattern wins. Empty matches are ignored.
    :param text: str, query text.
    :param patterns: regex patterns, or None.
    :return: (masked_text, spans), where spans[n-1] is the original text of token n.
    """
    patterns = expand_patterns(patterns)
    if not patterns:
        return text, []

    combined = re.compile('|'.join('(?:{})'.format(p) for p in patterns), re.ASCII)  # \w must not swallow CJK text
    spans, parts, last = [], [], 0
    for m in combined.finditer(text):
        if m.start() == m.end():
            continue
        spans.append(m.group(0))
        parts.append(text[last:m.start()])
        parts.append(_token(len(spans)))
        last = m.end()
    parts.append(text[last:])
    return ''.join(parts), spans


def restore(text: str, spans: List[str]) -> str:
    """
    Put the original spans back. Tokens match case-insensitively and tolerate inner spaces.
    :param text: str, engine output.
    :param spans: list returned by mask().
    :return: restored text.
    :raise PreserveError: a token is missing or appears more than once.
    """
    if not spans:
        return text

    problems = []
    for n in range(1, len(spans) + 1):
        cnt = len(_token_pattern(n).findall(text))
        if cnt != 1:
            problems.append('QX{}Z x{}'.format(n, cnt))
    if problems:
        raise PreserveError('placeholder tokens not kept exactly once: ' + ', '.join(problems))

    for n, span in enumerate(spans, 1):
        def _sub(m: 're.Match', _span: str = span) -> str:
            s = m.string
            left = '' if m.start() == 0 or s[m.start() - 1] in _NO_SPACE_AFTER else ' '
            right = '' if m.end() == len(s) or s[m.end()] in _NO_SPACE_BEFORE else ' '
            return left + _span + right

        text = _token_pattern(n).sub(_sub, text, count=1)
    return text
