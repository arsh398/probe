"""Provider adapter registry."""

from probe.runner.adapters.openai_adapter import OpenAIAdapter
from probe.runner.adapters.anthropic_adapter import AnthropicAdapter
from probe.runner.adapters.google_adapter import GoogleAdapter
from probe.runner.adapters.generic import GenericAdapter

_ADAPTERS = {
    "openai": OpenAIAdapter(),
    "anthropic": AnthropicAdapter(),
    "google": GoogleAdapter(),
    "generic": GenericAdapter(),
    "ollama": GenericAdapter(base_url="http://localhost:11434"),
}


def get_adapter(provider: str):
    """Return the adapter for the given provider name."""
    adapter = _ADAPTERS.get(provider.lower())
    if adapter is None:
        # Fall back to generic (OpenAI-compatible)
        return _ADAPTERS["generic"]
    return adapter
