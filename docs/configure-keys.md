# Configuring keyed engines

Most engines in this library need no setup. Nine engines call official translation APIs and only work with the user's own key: `deeplApi`, `azure`, `googleCloud`, `baiduApi`, `aliyunApi`, `caiyunApi`, `youdaoApi`, `niutransApi`, `volcEngineApi`. A keyed engine shows up in `translators_pool` only after its required fields are set. Until then the library behaves exactly as if it did not exist.

## Where credentials come from

Later sources override earlier ones:

1. The credentials file: `~/.config/translators/credentials.toml`, or the path in `$TRANSLATORS_CREDENTIALS`. One TOML table per engine. Keep it private (`chmod 600`); the library warns if other users can read it.
2. Environment variables named `TRANSLATORS_<ENGINE>_<FIELD>`, upper-cased, e.g. `TRANSLATORS_DEEPLAPI_API_KEY`, `TRANSLATORS_BAIDUAPI_SECRET_KEY`.
3. Keyword arguments on the call, e.g. `translate_text(..., translator='azure', api_key='...')`. These only override values. An unconfigured engine stays out of the pool.

### Which source to use

All three work on every OS and can be mixed per field.

| Situation | Use | Why |
| --- | --- | --- |
| Personal machine | `"@keyring"` in the file, secret in the OS credential store | Encrypted at rest and read only when the library needs it. An exported variable sits in plaintext in a shell profile and is inherited by every child process, including coding agents that may print their environment. |
| CI, containers, servers | Environment variables injected by the platform's secret store | No desktop credential store there; the platform keeps the secret off disk. |
| Quick local test | Plain value in the file, `chmod 600` | Simplest; the library warns if other users can read the file. |

### Keeping secrets in the OS credential store

A file value of `"@keyring"` means "read this from the operating system's credential store", using service `translators` and account `<engine>.<field>`. The file then holds no secret. `"@keychain"` is accepted as an alias.

```toml
[deeplApi]
api_key = "@keyring"

[azure]
api_key = "@keyring"
region = "australiaeast"
```

| OS | Store | Lookup | Write the secret (prompts, so it stays out of shell history) |
| --- | --- | --- | --- |
| macOS | login keychain | `/usr/bin/security`, nothing to install | `security add-generic-password -U -s translators -a deeplApi.api_key -w` |
| Windows | Credential Manager | `keyring` package: `pip install "translators[keyring]"` | `keyring set translators deeplApi.api_key` |
| Linux | Secret Service (GNOME Keyring, KWallet) | `keyring` package, needs a running Secret Service | `keyring set translators deeplApi.api_key` |

`keyring set` works on macOS too, once the package is installed. On macOS the library tries `security` first and then `keyring`. A missing item, or a missing `keyring` package on Windows/Linux, leaves the engine unconfigured with a warning.

Headless Linux servers and CI usually have no Secret Service. Use environment variables there.

The library reads credentials once at import. After editing the file or keychain, call `translators.refresh_keyed_engines()`, which returns the names of the configured keyed engines, or start a new process.

## Fields per engine

| Engine | Required fields | Optional fields | Where to get them |
| --- | --- | --- | --- |
| `deeplApi` | `api_key` | `host` | deepl.com account > API Keys & Limits. Keys ending in `:fx` use api-free.deepl.com |
| `azure` | `api_key` | `region`, `endpoint` | Azure portal > Translator resource (pricing tier F0) > Keys and Endpoint. Set `region` for a regional resource |
| `googleCloud` | `api_key` | | Google Cloud console > APIs & Services > Credentials > API key. Billing must be enabled |
| `baiduApi` | `appid`, `secret_key` | | fanyi-api.baidu.com > developer info |
| `aliyunApi` | `access_key_id`, `access_key_secret` | `endpoint` (default `mt.aliyuncs.com`) | Alibaba Cloud RAM > AccessKey. Use a RAM user limited to `alimt:TranslateGeneral` |
| `caiyunApi` | `token` | | platform.caiyunapp.com > tokens |
| `youdaoApi` | `app_key`, `app_secret` | | ai.youdao.com > application |
| `niutransApi` | `api_key` | | niutrans.com > console |
| `volcEngineApi` | `access_key_id`, `secret_access_key` | `region` (default `cn-north-1`) | Volcengine console > access keys |

Free quotas and overage rules change; see the table in the README. Alibaba Cloud and Google bill overage automatically, so set a budget alert there.

## Checking a configuration

```python
import translators as ts
print(ts.refresh_keyed_engines())          # e.g. ['deeplApi']
print(ts.translate_text('Run the tests before you push.', translator='deeplApi', to_language='zh'))
```

Put keyed engines in a fallback chain next to keyless ones, so a spent quota falls through instead of failing:

```python
ts.translate_text(text, translator=['deeplApi', 'azure', 'google', 'bing'], to_language='zh', preserve='code')
```

From the CLI: `fanyi 'Hello' --translator deeplApi,google --to zh`.

## Notes for coding agents

When a user asks you to set up a keyed engine:

- Never ask the user to paste a key into the chat, and never echo one into a command, log or file you show. Give them the store command for their OS (`security add-generic-password ... -w` on macOS, `keyring set translators <engine>.<field>` elsewhere) to run in their own terminal, or tell them to edit the credentials file with their editor.
- You may write the non-secret parts yourself: create `~/.config/translators/credentials.toml` with `chmod 600`, and add the engine's table with `"@keyring"` placeholders or empty values. On Windows/Linux also install the extra: `pip install "translators[keyring]"`.
- To verify, call `refresh_keyed_engines()` and run one short translation. Do not print the credential values. For DeepL, `GET https://api-free.deepl.com/v2/usage` with the `Authorization: DeepL-Auth-Key ...` header shows the remaining quota.
- A missing credential-store item or a missing required field leaves the engine out of the pool and emits a warning instead of raising.
