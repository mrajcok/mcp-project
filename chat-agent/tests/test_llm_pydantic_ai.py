# ABOUT-ME: Tests for the Pydantic AI runner using monkeypatch to avoid real network calls.
# ABOUT-ME: Ensures PydanticAiRunner uses the agent and returns LLMOut.

from src.rate_limiter import RateLimiter
from src.llm import PydanticAiRunner, LLMOut


def test_pydantic_ai_runner_basic(monkeypatch):
    rl = RateLimiter(max_ops=5, window_secs=60, max_concurrent=3)
    runner = PydanticAiRunner(username="ivy", rate_limiter=rl, api_key="sk-test")

    class FakeResult:
        output = "Here you go. {\"recommended_tool\": \"read_text_file\"}"

    class FakeAgent:
        def run_sync(self, prompt: str):
            return FakeResult()

    def fake_agent(self):
        return FakeAgent()

    monkeypatch.setattr(PydanticAiRunner, "_agent", fake_agent)

    out = runner.run_llm("hello")
    assert isinstance(out, LLMOut)
    assert out.text.startswith("Here you go.")
    assert out.recommended_tool == "read_text_file"

    # Rate limiter counted one op
    assert len(rl._state[runner.username].ops) == 1
