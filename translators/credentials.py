# coding=utf-8
# author=UlionTse

"""
Credentials for keyed (official API) engines.

A keyed engine joins `translators_pool` only when all its required fields are set. Sources, later wins:
  1. file: $TRANSLATORS_CREDENTIALS, else ~/.config/translators/credentials.toml
       [deeplApi]
       api_key = "xxxx:fx"
  2. environment: TRANSLATORS_<ENGINE>_<FIELD>, e.g. TRANSLATORS_DEEPLAPI_API_KEY
  3. keyword arguments of the engine call, e.g. api_key='...'
More keys for one engine: [engine.<label>] tables or TRANSLATORS_<ENGINE>_<FIELD>_<n>; see key_sets() and keyed.KeyRotation.
A file value of "@keyring" (alias "@keychain") is read from the OS credential store, service "translators",
account "<engine>.<field>": macOS keychain via /usr/bin/security, otherwise the optional `keyring` package
(Windows Credential Manager, Linux Secret Service). Store a secret with a prompt, so it stays out of history:
  keyring set translators deeplApi.api_key                             # any OS, needs `pip install keyring`
  security add-generic-password -U -s translators -a deeplApi.api_key -w   # macOS, no extra package
Keep the file private (chmod 600); a group/world-readable file triggers a warning.
"""

import os
import re
import stat
import warnings
import configparser
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

__all__ = ('KEYED_ENGINES', 'default_path', 'load', 'get', 'is_configured', 'KEYRING', 'keyring_lookup', 'key_sets', 'DEFAULT_LABEL')

# engine name -> (required fields, optional fields)
KEYED_ENGINES: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {}
KEYRING = ('@keyring', '@keychain')
KEYRING_SERVICE = 'translators'
_cache: Optional[Dict[str, Dict[str, str]]] = None
_sets: Optional[Dict[str, List[Tuple[str, Dict[str, str]]]]] = None
DEFAULT_LABEL = 'default'


def keyring_lookup(account: str) -> Optional[str]:
    """Read service `translators`, account `account` from the OS credential store; None if absent."""
    if sys.platform == 'darwin' and os.path.exists('/usr/bin/security'):
        r = subprocess.run(['/usr/bin/security', 'find-generic-password', '-s', KEYRING_SERVICE,
                            '-a', account, '-w'], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.rstrip('\n')
    try:
        import keyring
    except ImportError:
        if sys.platform != 'darwin':
            warnings.warn(f'{account} = "@keyring" needs the `keyring` package: pip install keyring')
            return None
    else:
        try:
            value = keyring.get_password(KEYRING_SERVICE, account)
        except Exception as e:  # no usable backend, locked store, ...
            warnings.warn(f'keyring lookup for {account} failed: {e}')
            return None
        if value:
            return value
    warnings.warn(f'No credential-store item for service "{KEYRING_SERVICE}", account "{account}".')
    return None


def default_path() -> str:
    return os.environ.get('TRANSLATORS_CREDENTIALS') or os.path.join(
        os.path.expanduser('~'), '.config', 'translators', 'credentials.toml')


def _read_file(path: str) -> Dict[str, Dict[str, str]]:
    if not os.path.isfile(path):
        return {}
    mode = os.stat(path).st_mode
    if os.name == 'posix' and mode & (stat.S_IRWXG | stat.S_IRWXO):
        warnings.warn(f'{path} is readable by other users; run `chmod 600 {path}`.')
    try:
        import tomllib  # Python 3.11+
        with open(path, 'rb') as f:
            data = tomllib.load(f)
        return {k: {fk: fv if isinstance(fv, dict) else str(fv) for fk, fv in v.items()}
                for k, v in data.items() if isinstance(v, dict)}
    except ImportError:
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str  # keep field case
        parser.read(path, encoding='utf-8')
        out: Dict[str, dict] = {}
        for s in parser.sections():
            fields = {k: v.strip().strip('"\'') for k, v in parser[s].items()}
            engine, _, label = s.partition('.')
            out.setdefault(engine, {}).update({label: fields} if label else fields)
        return out


def _resolve(engine: str, label: str, field: str, value: str) -> Optional[str]:
    if value in KEYRING:
        return keyring_lookup(f'{engine}.{label}.{field}' if label != DEFAULT_LABEL else f'{engine}.{field}')
    for prefix in KEYRING:
        if value.startswith(prefix + ':'):
            return keyring_lookup(value[len(prefix) + 1:])
    return value


def load(path: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """
    :param path: credentials file, default `default_path()`.
    :return: {engine: {field: value}} for each engine's first key set (see key_sets), merged from file and environment.
    """
    data = _read_file(path or default_path())
    out, sets = {}, {}
    for engine, (required, optional) in KEYED_ENGINES.items():
        raw = data.get(engine, {})
        base = {k: v for k, v in raw.items() if not isinstance(v, dict)}
        found = {DEFAULT_LABEL: base}
        for label, sub in raw.items():
            if isinstance(sub, dict):  # [engine.label]: another key set; inherits the optional fields of [engine]
                found[label] = {**{k: v for k, v in base.items() if k in optional}, **{k: str(v) for k, v in sub.items()}}
        prefix = 'TRANSLATORS_{}_'.format(re.sub(r'\W', '', engine).upper())
        for field in required + optional:
            for env, value in os.environ.items():
                m = re.fullmatch(re.escape(prefix + field.upper()) + r'(?:_(\d+))?', env)
                if m and value:
                    found.setdefault(m.group(1) or DEFAULT_LABEL, {})[field] = value
        resolved = []
        for label, fields in found.items():
            fields = {k: _resolve(engine, label, k, v) for k, v in fields.items()}
            fields = {k: v for k, v in fields.items() if v}
            if fields:
                resolved.append((label, fields))
        complete = [(lb, f) for lb, f in resolved if required and all(f.get(r) for r in required)]
        if resolved:
            out[engine] = (complete or resolved)[0][1]
        if complete:
            sets[engine] = complete
    global _cache, _sets
    _cache, _sets = out, sets
    return out


def key_sets(engine: str) -> List[Tuple[str, Dict[str, str]]]:
    """
    :return: [(label, fields)] of complete key sets in priority order: [engine] first, then [engine.<label>]
             tables in file order, then TRANSLATORS_<ENGINE>_<FIELD>_<n> environment sets.
    """
    if _sets is None:
        load()
    return list(_sets.get(engine, []))


def get(engine: str, field: str, kwargs: Optional[dict] = None, creds: Optional[dict] = None) -> Optional[str]:
    """Call kwargs win over loaded credentials."""
    if kwargs and kwargs.get(field):
        return kwargs[field]
    if creds is None:
        creds = _cache if _cache is not None else load()
    return creds.get(engine, {}).get(field)


def is_configured(engine: str, creds: Optional[dict] = None) -> bool:
    required = KEYED_ENGINES.get(engine, ((), ()))[0]
    fields = (creds if creds is not None else load()).get(engine, {})
    return bool(required) and all(fields.get(f) for f in required)
