"""Mutation operations for evolutionary test generation — pure structural, no AI."""

import random
from probe.claims.math_claims import Claim
from probe.pressure.templates import TemplateEngine


MutationType = str  # TEMPLATE_SWAP | LEVEL_SHIFT | DOMAIN_SWAP | DEPTH_MUTATION | CROSSOVER | ATTRIBUTION_SWAP


def template_swap(claim_text: str, level: int, engine: TemplateEngine) -> tuple[str, MutationType]:
    """TEMPLATE_SWAP: same claim, different pressure template from same level."""
    return engine.fill(claim_text, level), "TEMPLATE_SWAP"


def level_shift(claim_text: str, current_level: int, engine: TemplateEngine) -> tuple[str, int, MutationType]:
    """LEVEL_SHIFT: same claim, adjacent pressure level (prefer increasing)."""
    direction = 1 if current_level < 6 else -1
    new_level = max(0, min(7, current_level + direction))
    return engine.fill(claim_text, new_level), new_level, "LEVEL_SHIFT"


def depth_mutation(claim_text: str, level: int, engine: TemplateEngine) -> tuple[list[dict], MutationType]:
    """DEPTH_MUTATION: embed claim deeper in a multi-turn conversation."""
    return engine.fill_multi_turn(claim_text, level), "DEPTH_MUTATION"


def crossover(
    claim_text_a: str,
    level_a: int,
    claim_text_b: str,
    level_b: int,
    engine: TemplateEngine,
) -> tuple[str, MutationType]:
    """CROSSOVER: pressure level from test A, claim from test B."""
    return engine.fill(claim_text_b, level_a), "CROSSOVER"


def domain_swap(claim: Claim, engine: TemplateEngine, level: int) -> tuple[str, MutationType]:
    """
    DOMAIN_SWAP: same pressure framing, different claim domain.
    Generates a new claim of a different type and wraps it with the same pressure level.
    """
    from probe.claims import generate_claims

    # Exclude the current domain
    all_types = ["math", "logic", "science", "code"]
    other_types = [t for t in all_types if t != claim.category]
    new_type = random.choice(other_types)

    new_claims = generate_claims(total=1, claim_types=[new_type], control_ratio=0.0)
    if not new_claims:
        # Fallback: use same claim with template swap
        return engine.fill(claim.claim_text, level), "TEMPLATE_SWAP"

    new_claim = new_claims[0]
    return engine.fill(new_claim.claim_text, level), "DOMAIN_SWAP"


def attribution_swap(
    claim_text: str,
    level: int,
    engine: TemplateEngine,
    current_attribution: str | None = None,
) -> tuple[str, MutationType]:
    """ATTRIBUTION_SWAP: for subjective tests, change the attributed source."""
    # This is only meaningful for subjective tests — for objective claims, do a template swap
    return engine.fill(claim_text, level), "ATTRIBUTION_SWAP"


def apply_single_mutation(
    claim_text: str,
    level: int,
    engine: TemplateEngine,
    exclude: list[MutationType] | None = None,
) -> tuple[str, int, MutationType]:
    """Apply a single random mutation. Returns (new_claim_text, new_level, mutation_type)."""
    available = ["TEMPLATE_SWAP", "LEVEL_SHIFT", "DEPTH_MUTATION"]
    if exclude:
        available = [m for m in available if m not in exclude]

    mutation = random.choice(available)

    if mutation == "TEMPLATE_SWAP":
        text, mut = template_swap(claim_text, level, engine)
        return text, level, mut
    elif mutation == "LEVEL_SHIFT":
        text, new_level, mut = level_shift(claim_text, level, engine)
        return text, new_level, mut
    elif mutation == "DEPTH_MUTATION":
        msgs, mut = depth_mutation(claim_text, level, engine)
        # For depth mutation, return the last user message as the text
        user_msgs = [m["content"] for m in msgs if m["role"] == "user"]
        text = user_msgs[-1] if user_msgs else engine.fill(claim_text, level)
        return text, level, mut

    text, mut = template_swap(claim_text, level, engine)
    return text, level, mut
