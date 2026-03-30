"""Multi-turn conversation embedding for claims."""

from probe.pressure.templates import TemplateEngine


def embed_claim_in_conversation(claim: str, level: int, engine: TemplateEngine | None = None) -> list[dict]:
    """
    Embed a claim inside a multi-turn conversation at the given pressure level.
    Returns a list of message dicts for API calls.
    """
    if engine is None:
        engine = TemplateEngine()
    return engine.fill_multi_turn(claim, level)


def build_single_turn(claim: str, level: int, engine: TemplateEngine | None = None) -> list[dict]:
    """Build a single-turn message for the given claim and level."""
    if engine is None:
        engine = TemplateEngine()
    return [{"role": "user", "content": engine.fill(claim, level)}]
