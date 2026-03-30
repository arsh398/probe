"""Unified claim generation interface."""

import random
from probe.claims.math_claims import Claim, generate_math_claim_batch
from probe.claims.logic_claims import generate_logic_claim_batch
from probe.claims.science_claims import generate_science_claim_batch
from probe.claims.code_claims import generate_code_claim_batch
from probe.config import CLAIM_TYPE_WEIGHTS, CONTROL_RATIO

__all__ = ["Claim", "generate_claims"]

_GENERATORS = {
    "math": generate_math_claim_batch,
    "logic": generate_logic_claim_batch,
    "science": generate_science_claim_batch,
    "code": generate_code_claim_batch,
}


def generate_claims(
    total: int = 500,
    claim_types: list[str] | None = None,
    control_ratio: float = CONTROL_RATIO,
) -> list[Claim]:
    """
    Generate a balanced mix of claims across the specified types.

    Args:
        total: Total number of claims to generate.
        claim_types: List of types to include. None = all types.
        control_ratio: Fraction of claims that present the TRUE statement (controls).

    Returns:
        Shuffled list of Claim objects.
    """
    if claim_types is None:
        claim_types = list(CLAIM_TYPE_WEIGHTS.keys())

    # Validate types
    invalid = [t for t in claim_types if t not in _GENERATORS]
    if invalid:
        raise ValueError(f"Unknown claim types: {invalid}. Valid: {list(_GENERATORS.keys())}")

    # Compute per-type weights
    weights = {t: CLAIM_TYPE_WEIGHTS.get(t, 1.0) for t in claim_types}
    total_weight = sum(weights.values())
    normalized = {t: w / total_weight for t, w in weights.items()}

    # Distribute counts
    counts: dict[str, int] = {}
    allocated = 0
    types_list = list(normalized.items())

    for i, (t, w) in enumerate(types_list):
        if i == len(types_list) - 1:
            counts[t] = total - allocated
        else:
            counts[t] = round(total * w)
            allocated += counts[t]

    # Generate per type
    all_claims: list[Claim] = []
    for t, count in counts.items():
        if count <= 0:
            continue
        gen = _GENERATORS[t]
        claims = gen(n=count, control_ratio=control_ratio)
        all_claims.extend(claims)

    random.shuffle(all_claims)
    return all_claims
