# ABOUT-ME: Stateless LLM integration helpers using a simple callable interface.
# ABOUT-ME: Provides run_llm(user_input, caller) and a Pydantic AI-backed runner for OpenAI.

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Any
import importlib
import json
import re

from pydantic import BaseModel

from .rate_limiter import RateLimiter


class LLMOut(BaseModel):
    text: str
    recommended_tool: Optional[str] = None


class LLMCaller(Protocol):
    def __call__(self, prompt: str) -> dict:
        """
        Executes an LLM call and returns a dict with at least {'text': str} and
        optionally {'recommended_tool': str}.
        """
        ...


@dataclass
class LLMRunner:
    """Small wrapper to enforce one operation per call via RateLimiter.

    Inputs:
    - username: str used for rate limiting
    - rate_limiter: RateLimiter instance
    - caller: a callable that actually talks to the LLM (mock in tests)

    Output:
    - LLMOut model with text and optional recommended_tool
    """

    username: str
    rate_limiter: RateLimiter
    caller: LLMCaller

    def run_llm(self, user_input: str) -> LLMOut:
        # Count one operation
        self.rate_limiter.record_operation(self.username)

        # Stateless call: just send the user input
        result = self.caller(user_input)
        text = result.get("text", "")
        rec_tool = result.get("recommended_tool")
        return LLMOut(text=text, recommended_tool=rec_tool or None)


@dataclass
class PydanticAiRunner:
    """Pydantic AI + OpenAI-backed LLM runner.

    Inputs:
    - username: used for rate limiting
    - rate_limiter: RateLimiter instance
    - api_key: OpenAI API key
    - model: OpenAI model name, e.g., 'gpt-4o-mini'

    Behavior:
    - Stateless call using a minimal system prompt and the user's input.
    - Returns LLMOut with optional recommended_tool if present in the model output JSON.
    """

    username: str
    rate_limiter: RateLimiter
    api_key: str
    model: str = "gpt-4o-mini"
    system_prompt: str = (
        "You are a helpful assistant. If you recommend using a tool, "
        "respond with a short answer and include a JSON line like: {\"recommended_tool\": \"tool_name\"}."
    )

    def _agent(self):  # returns a pydantic_ai.Agent instance at runtime
    # Deferred import via importlib to avoid hard dependency at module import time

        p_ai = importlib.import_module("pydantic_ai")
        openai_mod = importlib.import_module("pydantic_ai.models.openai")
        Agent = getattr(p_ai, "Agent")
        OpenAIModel = getattr(openai_mod, "OpenAIModel")

        openai_model = OpenAIModel(self.model, api_key=self.api_key)
        return Agent(openai_model, system_prompt=self.system_prompt)

    def run_llm(self, user_input: str) -> LLMOut:
        # Count one operation
        self.rate_limiter.record_operation(self.username)

        agent = self._agent()
        # Pydantic AI returns different result shapes depending on agent settings.
        result = agent.run_sync(user_input)

        # Extract the text from result using explicit, supported paths.
        def _safe_str(x):
            try:
                return str(x)
            except Exception:
                return ""

        # Only use the documented AgentRunResult.output attribute.
        # Projects using this runner should rely on pydantic-ai's documented API.
        text = ""
        val = getattr(result, "output", None)
        if val is not None:
            if isinstance(val, str):
                text = val.strip()
            else:
                # stringify non-string outputs while keeping behavior minimal
                try:
                    text = str(val).strip()
                except Exception:
                    text = ""

        # Best-effort extraction of recommended_tool if present as JSON in the text
        rec_tool: Optional[str] = None
        try:

            # Find a JSON object within the response
            match = re.search(r"\{[^\{\}]*\}", text)
            if match:
                candidate = json.loads(match.group(0))
                if isinstance(candidate, dict):
                    val = candidate.get("recommended_tool")
                    if isinstance(val, str) and val:
                        rec_tool = val
        except Exception:
            # Ignore parsing errors; only the text is required
            pass

        return LLMOut(text=text, recommended_tool=rec_tool)
