# ABOUT-ME: Integration tests that call the real Pydantic AI + OpenAI LLM.
# ABOUT-ME: Skipped unless OPENAI_API_KEY is present; marked as integration.

import os
import asyncio
import pytest

from src.agent import AgentManager


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY in environment"
)
def test_real_llm_responds_minimally():
    # Use the real pydantic_ai Agent through AgentManager
    cfg = {"mcp_servers": []}
    mgr = AgentManager(config=cfg)
    # Determine effective model name (default to gpt-4o-mini)
    model_name = os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
    print(f"DEBUG: effective OPENAI_MODEL used: {model_name}")

    mgr.initialize_llm(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model=model_name,
        system_prompt=os.environ.get("SYSTEM_PROMPT"),
    )

    agent = mgr.llm
    assert agent is not None

    # Diagnostic prints: environment and agent introspection
    #print(f"DEBUG: OPENAI_MODEL: {os.environ.get('OPENAI_MODEL')} ")
    #print(f"DEBUG: SYSTEM_PROMPT set: {bool(os.environ.get('SYSTEM_PROMPT'))}")

    # list a few attributes without dumping enormous objects
    #atts = [a for a in dir(agent) if not a.startswith("_")][:40]
    #print(f"DEBUG: agent public attrs (sample): {atts}")
    # Try to find model-like attributes on the Agent
    model_like = None
    for name in ("model", "_model", "model_obj", "deps", "dependency", "_deps"):
        if hasattr(agent, name):
            model_like = getattr(agent, name)
            print(f"DEBUG: agent.{name} -> {type(model_like)!r}")
            break

    # Run the agent with extra diagnostics; capture exceptions
    try:
        result = asyncio.run(agent.run("Reply with the single word OK."))
    except Exception as e:  # show full exception info for debugging
        import traceback

        print("DEBUG: agent.run raised exception:")
        traceback.print_exc()
        raise

    # The call should complete without exceptions and return a result object
    assert result is not None
    # Print the raw result repr and known fields to inspect provider response
    try:
        print(f"DEBUG: raw result repr: {result!r}")
    except Exception:
        print("DEBUG: result repr() failed")
    print(f"LLM output: {result.output}")
