"""Restricted text-only LiteLLM/OpenAI-compatible call for Plan/Design."""
import json
import os
from urllib.request import Request, urlopen
from urllib.parse import urlsplit


class ModelConfigurationError(ValueError):
    pass


def invoke_role(*, role_instruction: str, objective: str, input_text: str = "", timeout: int = 45) -> tuple[str, str]:
    """No tool calls; returns model text and alias. Secrets stay in environment."""
    base = os.environ.get("HERMES_LITELLM_BASE_URL", "").rstrip("/")
    key = os.environ.get("HERMES_LITELLM_API_KEY", "")
    model = os.environ.get("HERMES_MODEL_ALIAS", "")
    if not base or not key or not model:
        raise ModelConfigurationError("Set HERMES_LITELLM_BASE_URL, HERMES_LITELLM_API_KEY and HERMES_MODEL_ALIAS")
    parsed = urlsplit(base)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}):
        raise ModelConfigurationError("HTTPS is required except for localhost development")
    route = base + ("/chat/completions" if parsed.path.rstrip("/").endswith("/v1") else "/v1/chat/completions")
    messages = [{"role": "system", "content": role_instruction + "\nWrite only the stage artifact. Never claim approval."},
                {"role": "user", "content": "Objective:\n" + objective + "\nPrevious artifact:\n" + input_text[:24000]}]
    body = json.dumps({"model": model, "messages": messages, "temperature": 0.2,
                       "max_tokens": 2200, "stream": False}).encode("utf-8")
    request = Request(route, data=body, headers={"Content-Type": "application/json",
                                                    "Authorization": "Bearer " + key}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        result = json.load(response)
    text = result["choices"][0]["message"]["content"]
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Provider returned no text artifact")
    return text, model
