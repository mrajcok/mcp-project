# ABOUT-ME: Tests for stateless LLM integration wrapper and tool suggestion plumbing.
# ABOUT-ME: Verifies single operation per call and structured return shape.

from src.rate_limiter import RateLimiter
from src.llm import LLMRunner


def test_run_llm_returns_text_and_optional_tool_and_counts_one_op():
    rl = RateLimiter(max_ops=5, window_secs=60, max_concurrent=3)
    user = "zoe"

    calls = {"count": 0}

    def fake_llm(prompt: str):
        calls["count"] += 1
        # Echo prompt with a suggestion
        return {"text": f"Echo: {prompt}", "recommended_tool": "read_text_file"}

    runner = LLMRunner(username=user, rate_limiter=rl, caller=fake_llm)

    # Before call, zero ops recorded
    assert len(rl._state[user].ops) == 0

    out = runner.run_llm("hello")

    assert out.text == "Echo: hello"
    assert out.recommended_tool == "read_text_file"

    # One LLM call made
    assert calls["count"] == 1

    # Exactly one operation recorded for rate limit
    assert len(rl._state[user].ops) == 1
