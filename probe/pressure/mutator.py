"""Structural mutations for pressure templates (used by evolution engine)."""

import random
from probe.pressure.templates import TemplateEngine


def mutate_template_swap(claim: str, level: int, engine: TemplateEngine) -> str:
    """TEMPLATE_SWAP: same claim, different template from the same level."""
    return engine.fill(claim, level)


def mutate_level_shift(claim: str, current_level: int, engine: TemplateEngine, direction: int = 1) -> tuple[str, int]:
    """
    LEVEL_SHIFT: same claim, adjacent pressure level.
    Returns (filled_text, new_level).
    """
    new_level = max(0, min(7, current_level + direction))
    return engine.fill(claim, new_level), new_level


def mutate_depth(claim: str, level: int, engine: TemplateEngine, depth: int | None = None) -> list[dict]:
    """
    DEPTH_MUTATION: embed claim deeper or shallower in a conversation.
    Returns message list.
    """
    # depth param is informational — actual depth is controlled by conversation templates
    return engine.fill_multi_turn(claim, level)
