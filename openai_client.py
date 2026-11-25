import requests

DEFAULT_BASE_URL = "http://localhost:8080/v1"


def normalize_base_url(url):
    """Return a base URL ending in exactly one /v1, with no query or trailing slash."""
    url = (url or "").strip()
    if not url:
        url = DEFAULT_BASE_URL
    url = url.rstrip("/")
    if url.endswith("/chat/completions"):
        url = url[: -len("/chat/completions")]
    if not url.endswith("/v1"):
        url = url + "/v1"
    return url


class OpenAIClient:
    """Minimal OpenAI-compatible chat client.

    Works with llama-server, llama-swap, vLLM, LM Studio, Ollama's /v1 and OpenAI.
    The API key is optional because local servers do not require one.
    """

    def __init__(self, base_url=DEFAULT_BASE_URL, model="qwen3.6-35b-a3b",
                 api_key="", timeout=120, disable_thinking=True):
        self.base_url = normalize_base_url(base_url)
        self.api_url = self.base_url + "/chat/completions"
        self.model = model
        self.api_key = (api_key or "").strip()
        self.timeout = timeout
        self.disable_thinking = disable_thinking

    def ask(self, question):
        """Ask a general question and return the response text."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Give concise, direct answers. "
                    "Use plain text only, no markdown formatting. "
                    "Keep responses short (2-3 sentences max)."
                ),
            },
            {"role": "user", "content": question},
        ]
        return self._call_api(messages, max_tokens=800)

    def synonyms(self, word):
        """Return a list of synonyms for the given word."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a synonym finder. Given a word, return only a "
                    "comma-separated list of synonyms. No explanations, no "
                    "numbering, no extra text. Just the synonyms separated by commas."
                ),
            },
            {"role": "user", "content": word},
        ]
        response = self._call_api(messages, max_tokens=200)
        return [s.strip() for s in response.split(",") if s.strip()]

    def _call_api(self, messages, max_tokens):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer %s" % self.api_key

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        if self.disable_thinking:
            # Qwen3* and similar hybrid reasoning templates spend the whole
            # max_tokens budget on reasoning_content, leaving `content` empty,
            # which renders as a blank result list. llama.cpp / llama-swap
            # honour this flag.
            payload["chat_template_kwargs"] = {"enable_thinking": False}

        response = requests.post(
            self.api_url, headers=headers, json=payload, timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0].get("message") or {}
        content = (message.get("content") or "").strip()
        if not content:
            content = (message.get("reasoning_content") or "").strip()
        if not content:
            content = ("No answer returned - the model may have used its whole "
                       "token budget on reasoning.")
        return content
