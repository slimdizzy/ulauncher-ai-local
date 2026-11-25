import logging

import requests
from openai_client import OpenAIClient, DEFAULT_BASE_URL
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction

ICON = "images/icon.svg"
logger = logging.getLogger(__name__)


class AiExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        query = event.get_argument()
        keyword = event.get_keyword()

        if keyword == extension.preferences["ai_kw"]:
            return self._handle_ai(query, extension)
        elif keyword == extension.preferences["syn_kw"]:
            return self._handle_synonyms(query, extension)

    def _handle_ai(self, query, extension):
        if not query:
            return self._render([self._info_item("Type your question...", "ai <question>")])

        client = self._get_client(extension)
        try:
            response = client.ask(query)
        except Exception as e:
            return self._render([self._make_error_item(e, client)])

        max_results = self._get_int(extension, "max_results", 5)
        return self._render(self._split_response(response, max_results))

    def _handle_synonyms(self, query, extension):
        if not query:
            return self._render([self._info_item("Type a word...", "syn <word>")])

        client = self._get_client(extension)
        try:
            synonyms = client.synonyms(query)
        except Exception as e:
            return self._render([self._make_error_item(e, client)])

        if not synonyms:
            return self._render([self._info_item("No synonyms found", query)])

        max_results = self._get_int(extension, "max_results", 5)
        items = []
        for syn in synonyms[:max_results]:
            items.append(
                ExtensionResultItem(
                    icon=ICON,
                    name=syn,
                    description="Press Enter to copy",
                    on_enter=CopyToClipboardAction(syn),
                )
            )
        return self._render(items)

    def _get_client(self, extension):
        base_url = extension.preferences.get("server_url", "").strip() or DEFAULT_BASE_URL
        model = extension.preferences.get("model", "").strip()
        api_key = extension.preferences.get("api_key", "").strip()
        disable_thinking = str(
            extension.preferences.get("disable_thinking", "true")
        ).lower() in ("1", "true", "yes", "on")
        timeout = self._get_int(extension, "timeout", 120)
        return OpenAIClient(
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout=timeout,
            disable_thinking=disable_thinking,
        )

    def _get_int(self, extension, key, fallback):
        try:
            return int(str(extension.preferences.get(key, fallback)).strip())
        except (TypeError, ValueError):
            return fallback

    def _split_response(self, response, max_results):
        """Split a response into chunks for display as multiple result items."""
        full_response = response
        chunks = []
        while response:
            if len(response) <= 100:
                chunks.append(response)
                break
            split_at = response.rfind(" ", 0, 100)
            if split_at <= 0:
                split_at = 100
            chunks.append(response[:split_at])
            response = response[split_at:].lstrip()

        items = []
        for chunk in chunks[:max_results]:
            items.append(
                ExtensionResultItem(
                    icon=ICON,
                    name=chunk,
                    description="Press Enter to copy full response",
                    on_enter=CopyToClipboardAction(full_response),
                )
            )
        return items

    def _make_error_item(self, exception, client=None):
        """Create an error item based on the exception type."""
        where = client.api_url if client else "the configured server"
        if isinstance(exception, requests.exceptions.Timeout):
            return self._error_item("Request timed out - is the model still loading?")
        if isinstance(exception, requests.exceptions.ConnectionError):
            return self._error_item("Cannot reach %s" % where)
        if isinstance(exception, requests.exceptions.HTTPError):
            status = getattr(exception.response, "status_code", None)
            if status == 401:
                return self._error_item("Server rejected the API key (HTTP 401)")
            if status == 404:
                return self._error_item("Model or endpoint not found (HTTP 404) - check Server URL and Model")
            if status == 429:
                return self._error_item("Server busy or rate limited (HTTP 429)")
            body = ""
            try:
                body = (exception.response.text or "").strip()[:80]
            except Exception:
                pass
            return self._error_item("API error (HTTP %s) %s" % (status, body))
        if isinstance(exception, ValueError):
            return self._error_item("Unexpected response from %s" % where)
        logger.error("Unexpected error: %s", exception)
        return self._error_item("Unexpected error: %s" % str(exception)[:80])

    @staticmethod
    def _error_item(message):
        return ExtensionResultItem(
            icon=ICON,
            name=message,
            description="Check extension preferences",
            on_enter=DoNothingAction(),
        )

    @staticmethod
    def _info_item(name, description):
        return ExtensionResultItem(
            icon=ICON,
            name=name,
            description=description,
            on_enter=DoNothingAction(),
        )

    @staticmethod
    def _render(items):
        return RenderResultListAction(items)


if __name__ == "__main__":
    AiExtension().run()
