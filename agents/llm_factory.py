"""
Deterministic test-only mock with basic identifier-pattern checks.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Katz Hyperglycemia Sodium Corrector"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (f"[{self.system_name} mock interface] No clinical analysis or verification "
                f"was performed. Received query preview: '{prompt[:60]}...'.")


class LLMFactory:
    """Provide a mock response, rejecting unimplemented external providers."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Katz Hyperglycemia Sodium Corrector"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(
            f"Provider {provider!r} is not implemented. "
            "Only the deterministic mock backend is available."
        )
