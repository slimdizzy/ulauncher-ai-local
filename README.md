# Ulauncher Local AI Assistant

A fork of [laercioskt/ulauncher-ai](https://github.com/laercioskt/ulauncher-ai) that talks to **any OpenAI-compatible server** instead of only api.openai.com. No cloud dependency, no API key needed for a local box.

Point it at llama-server, llama-swap, vLLM, LM Studio, LocalAI, Ollama (`/v1`), or OpenAI itself.

## Install

```bash
git clone https://github.com/slimdizzy/ulauncher-ai-local.git \
  ~/.local/share/ulauncher/extensions/com.github.slimdizzy.ulauncher-ai-local
```

Then restart Ulauncher (or Extensions -> Reload in preferences). There is no build step.

## Preferences

| Preference | Default | Notes |
| --- | --- | --- |
| Server URL | `http://localhost:8080/v1` | `/v1` is added automatically, so `http://host:8080` works too |
| Model | `qwen3.6-35b-a3b` | On llama-swap this must be the **model id / swap key**, not the GGUF filename. Servers that ignore the name are fine with anything |
| API Key | *(empty)* | Optional. Only sent when non-empty |
| Disable model thinking | On | Sends `chat_template_kwargs.enable_thinking=false` |
| Timeout | `120` | A cold model load can take 30-60s |
| Max Results | `5` | Result items rendered per answer |

Typical setups:

- **llama-swap router** (multiple models behind one port): `http://<host>:8080/v1`, model = the swap key.
- **Single llama-server**: `http://<host>:8082/v1`, model name is usually ignored.

Use a LAN IP or a resolvable name in the Server URL. Hostnames that only exist
on a VPN mesh will not resolve on a laptop that is off the mesh, and a URL that
cannot resolve looks exactly like a broken extension.

## Usage

```
ai What is the capital of France?
ai explain recursion in one sentence
syn happy
```

Enter on any item copies the **full** response to the clipboard. Warm responses
come back in a few hundred milliseconds; the first query after a model has been
unloaded is the slow one.

## Why this fork exists

Three things in the original break on a self-hosted server:

1. `API_URL` was a hardcoded class constant pointing at api.openai.com. It is now a configurable base URL with `/v1` normalisation, which guards against the classic `http://host:8080/v1/v1/chat/completions`.
2. An empty API key aborted the request with "OpenAI API key not configured". Local servers don't use keys, so the key is optional and the header is only sent when set.
3. The 10s timeout and 300-token budget are too small for a local model: `timeout` is a preference now and `max_tokens` is 800. Reasoning models (Qwen3 family) also return an **empty string** at 300 tokens because the whole budget goes to `reasoning_content` - hence `enable_thinking=false`, with a fallback to `reasoning_content` for backends that ignore the flag.

Note that Ulauncher 5.x preference types are limited to `keyword`, `input`, `text`
and `select` - there is no `checkbox`, and an invalid type stops the whole
extension from loading.

## License

MIT, same as upstream. Upstream author: Laercio Pereira.
