import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.models import Provider


@dataclass
class ModelCallResult:
    ok: bool
    content: str
    parsed: dict[str, Any] | None = None
    error: str | None = None
    raw: dict[str, Any] | None = None


class ModelGateway:
    """Provider abstraction for LiteLLM/OpenAI-compatible/local/mock model calls.

    The gateway intentionally returns metadata and validated content only. It does
    not log prompt text because matter records can contain sensitive legal files.
    """

    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout

    async def complete(
        self,
        provider: Provider | None,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1600,
        strict_json: bool = True,
        schema_hint: dict[str, Any] | None = None,
    ) -> ModelCallResult:
        if provider is None or provider.provider_type == "mock":
            return self.mock_completion(messages, strict_json=strict_json, schema_hint=schema_hint)

        if not provider.enabled:
            return ModelCallResult(ok=False, content="", error="Provider is disabled.")

        try:
            if provider.provider_type in {"openai_api_key", "openai_oauth", "litellm_proxy", "local_openai_compatible"}:
                return await self.openai_compatible(provider, messages, temperature, max_tokens, strict_json)
            if provider.provider_type == "anthropic":
                return await self.anthropic(provider, messages, temperature, max_tokens)
            return ModelCallResult(ok=False, content="", error=f"Unsupported provider type: {provider.provider_type}")
        except Exception as exc:
            return ModelCallResult(ok=False, content="", error=f"{exc.__class__.__name__}: {exc}")

    async def openai_compatible(
        self,
        provider: Provider,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        strict_json: bool,
    ) -> ModelCallResult:
        base_url = (provider.base_url or "https://api.openai.com").rstrip("/")
        url = f"{base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if provider.api_key:
            headers["Authorization"] = f"Bearer {provider.api_key}"
        elif provider.provider_type == "local_openai_compatible":
            headers["Authorization"] = "Bearer local"
        body: dict[str, Any] = {
            "model": provider.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if strict_json and provider.supports_structured_output:
            body["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            payload = response.json()
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
        return ModelCallResult(ok=True, content=content, parsed=parse_json_object(content), raw=safe_raw(payload))

    async def anthropic(
        self,
        provider: Provider,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ModelCallResult:
        url = (provider.base_url or "https://api.anthropic.com").rstrip("/") + "/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if provider.api_key:
            headers["x-api-key"] = provider.api_key
        system = "\n".join(message["content"] for message in messages if message["role"] == "system")
        user_messages = [message for message in messages if message["role"] != "system"]
        body = {
            "model": provider.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": user_messages or [{"role": "user", "content": "Return a JSON status object."}],
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            payload = response.json()
        content = "\n".join(part.get("text", "") for part in payload.get("content", []) if part.get("type") == "text")
        return ModelCallResult(ok=True, content=content, parsed=parse_json_object(content), raw=safe_raw(payload))

    def mock_completion(
        self,
        messages: list[dict[str, str]],
        strict_json: bool,
        schema_hint: dict[str, Any] | None = None,
    ) -> ModelCallResult:
        joined = "\n".join(message["content"][:500] for message in messages[-2:])
        payload = {
            "claim": "Mock provider completed a schema-bound local turn.",
            "analysis": joined[:900],
            "cited_record_support": [],
            "cited_authority_support": [],
            "assumptions": ["Mock output should be replaced by a configured provider for substantive legal analysis."],
            "confidence": "medium",
            "newly_discovered_vulnerability": None,
        }
        return ModelCallResult(ok=True, content=json.dumps(payload), parsed=payload)

    async def diagnostic(self, provider: Provider, kind: str) -> dict[str, Any]:
        if kind == "connection":
            if provider.provider_type == "mock":
                return {
                    "ok": True,
                    "kind": kind,
                    "message": "Mock provider is available.",
                    "estimated_context_window": provider.context_window,
                    "supports_json_schema": provider.supports_structured_output,
                }
            result = await self.complete(
                provider,
                [{"role": "user", "content": "Return the word ok."}],
                max_tokens=20,
                strict_json=False,
            )
        elif kind == "structured_output":
            result = await self.complete(
                provider,
                [
                    {
                        "role": "user",
                        "content": 'Return only JSON with fields "status" and "risk".',
                    }
                ],
                max_tokens=120,
                strict_json=True,
            )
        else:
            result = await self.complete(
                provider,
                [{"role": "user", "content": "Summarize the purpose of a legal record stress test in one sentence."}],
                max_tokens=120,
                strict_json=False,
            )
        return {
            "ok": result.ok,
            "kind": kind,
            "message": "Diagnostic completed." if result.ok else "Diagnostic failed.",
            "response_preview": result.content[:400] if result.content else None,
            "supports_json_schema": provider.supports_structured_output,
            "estimated_context_window": provider.context_window,
            "last_error": result.error,
        }


def parse_json_object(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        match = content.find("{")
        end = content.rfind("}")
        if match >= 0 and end > match:
            try:
                parsed = json.loads(content[match : end + 1])
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None
    return None


def safe_raw(payload: dict[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage") if isinstance(payload, dict) else None
    return {"usage": usage} if usage else {}

