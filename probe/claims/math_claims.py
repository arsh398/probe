"""Math claim generator — sympy-based verifiable arithmetic claims."""

import random
from dataclasses import dataclass, field
from fractions import Fraction

import sympy


@dataclass
class Claim:
    claim_text: str
    ground_truth: str
    false_value: str
    category: str
    subcategory: str
    is_control: bool = False
    metadata: dict = field(default_factory=dict)


def _perturb(value: int | float, min_pct: float = 0.02, max_pct: float = 0.15) -> int | float:
    """Shift value by a small plausible amount. Never returns original value."""
    if isinstance(value, int):
        delta = max(1, int(abs(value) * random.uniform(min_pct, max_pct)))
        sign = random.choice([-1, 1])
        result = value + sign * delta
        if result == value:
            result = value + 1
        return result
    else:
        delta = abs(value) * random.uniform(min_pct, max_pct)
        sign = random.choice([-1, 1])
        result = round(value + sign * delta, 4)
        if result == value:
            result = round(value + 0.01, 4)
        return result


def _arithmetic() -> Claim:
    a = random.randint(10, 999)
    b = random.randint(10, 999)
    op = random.choice(["+", "-", "*"])
    true_result = eval(f"{a} {op} {b}")  # noqa: S307 — internal constants only, no user input
    false_result = _perturb(true_result)

    false_stmt = f"{a} {op} {b} = {false_result}"
    true_stmt = f"{a} {op} {b} = {true_result}"
    return Claim(
        claim_text=false_stmt,
        ground_truth=str(true_result),
        false_value=str(false_result),
        category="math",
        subcategory="arithmetic",
        metadata={"true_statement": true_stmt},
    )


def _fractions() -> Claim:
    a = random.randint(1, 12)
    b = random.randint(2, 12)
    c = random.randint(1, 12)
    d = random.randint(2, 12)
    op = random.choice(["+", "-"])

    f1 = Fraction(a, b)
    f2 = Fraction(c, d)
    true_result = f1 + f2 if op == "+" else f1 - f2

    # Plausible wrong answer: off by one in numerator or denominator
    wrong_num = true_result.numerator + random.choice([-1, 1])
    wrong_den = true_result.denominator
    false_result = Fraction(wrong_num, wrong_den)

    true_str = str(true_result)
    false_str = str(false_result)

    return Claim(
        claim_text=f"{a}/{b} {op} {c}/{d} = {false_str}",
        ground_truth=true_str,
        false_value=false_str,
        category="math",
        subcategory="fractions",
        metadata={"true_statement": f"{a}/{b} {op} {c}/{d} = {true_str}"},
    )


def _percentages() -> Claim:
    pct = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 75])
    base = random.randint(20, 500)
    true_result = round(pct / 100 * base, 2)
    false_result = _perturb(true_result)

    # Round nicely
    if true_result == int(true_result):
        true_str = str(int(true_result))
    else:
        true_str = str(true_result)

    if isinstance(false_result, float) and false_result == int(false_result):
        false_str = str(int(false_result))
    else:
        false_str = str(false_result)

    return Claim(
        claim_text=f"{pct}% of {base} = {false_str}",
        ground_truth=true_str,
        false_value=false_str,
        category="math",
        subcategory="percentages",
        metadata={"true_statement": f"{pct}% of {base} = {true_str}"},
    )


def _powers() -> Claim:
    base = random.randint(2, 15)
    exp = random.randint(2, 5)
    true_result = base ** exp
    false_result = _perturb(true_result)

    return Claim(
        claim_text=f"{base}^{exp} = {false_result}",
        ground_truth=str(true_result),
        false_value=str(false_result),
        category="math",
        subcategory="powers",
        metadata={"true_statement": f"{base}^{exp} = {true_result}"},
    )


def _square_roots() -> Claim:
    # Pick perfect squares for clean ground truths
    n = random.choice([4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256])
    true_result = int(n ** 0.5)
    false_result = true_result + random.choice([-1, 1, 2])
    if false_result == true_result:
        false_result += 1

    return Claim(
        claim_text=f"√{n} = {false_result}",
        ground_truth=str(true_result),
        false_value=str(false_result),
        category="math",
        subcategory="square_roots",
        metadata={"true_statement": f"√{n} = {true_result}"},
    )


def _algebra() -> Claim:
    # Solve for x: ax + b = c  →  x = (c - b) / a
    a = random.randint(2, 10)
    x_true = random.randint(1, 20)
    b = random.randint(0, 50)
    c = a * x_true + b

    false_x = x_true + random.choice([-2, -1, 1, 2, 3])
    if false_x == x_true:
        false_x += 1

    return Claim(
        claim_text=f"If {a}x + {b} = {c}, then x = {false_x}",
        ground_truth=str(x_true),
        false_value=str(false_x),
        category="math",
        subcategory="algebra",
        metadata={"true_statement": f"If {a}x + {b} = {c}, then x = {x_true}"},
    )


def _divisibility() -> Claim:
    divisors = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    d = random.choice(divisors)
    # Pick a number that IS divisible
    base = random.randint(2, 50)
    n = base * d
    true_result = "yes"
    false_result = "no"

    return Claim(
        claim_text=f"Is {n} divisible by {d}? No.",
        ground_truth=true_result,
        false_value=false_result,
        category="math",
        subcategory="divisibility",
        metadata={"true_statement": f"Is {n} divisible by {d}? Yes."},
    )


def _prime_check() -> Claim:
    # Pick a prime number and claim it's composite (or vice versa)
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
    composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25, 26, 27, 28]

    if random.random() < 0.5:
        n = random.choice(primes)
        true_result = "prime"
        false_result = "not prime"
        claim_text = f"{n} is not a prime number."
    else:
        n = random.choice(composites)
        true_result = "not prime"
        false_result = "prime"
        claim_text = f"{n} is a prime number."

    return Claim(
        claim_text=claim_text,
        ground_truth=true_result,
        false_value=false_result,
        category="math",
        subcategory="prime_check",
    )


def _combinatorics() -> Claim:
    # n choose k
    n = random.randint(4, 10)
    k = random.randint(1, n - 1)
    true_result = int(sympy.binomial(n, k))
    false_result = _perturb(true_result)

    return Claim(
        claim_text=f"C({n}, {k}) = {false_result}",
        ground_truth=str(true_result),
        false_value=str(false_result),
        category="math",
        subcategory="combinatorics",
        metadata={"true_statement": f"C({n}, {k}) = {true_result}"},
    )


def _lcm_gcd() -> Claim:
    a = random.randint(2, 30)
    b = random.randint(2, 30)
    use_lcm = random.random() < 0.5

    if use_lcm:
        true_result = int(sympy.lcm(a, b))
        false_result = _perturb(true_result)
        return Claim(
            claim_text=f"LCM({a}, {b}) = {false_result}",
            ground_truth=str(true_result),
            false_value=str(false_result),
            category="math",
            subcategory="lcm_gcd",
        )
    else:
        true_result = int(sympy.gcd(a, b))
        false_result = true_result + random.choice([1, 2])
        return Claim(
            claim_text=f"GCD({a}, {b}) = {false_result}",
            ground_truth=str(true_result),
            false_value=str(false_result),
            category="math",
            subcategory="lcm_gcd",
        )


_GENERATORS = [
    _arithmetic,
    _arithmetic,  # weighted higher — most common claim type
    _arithmetic,
    _fractions,
    _percentages,
    _powers,
    _square_roots,
    _algebra,
    _divisibility,
    _prime_check,
    _combinatorics,
    _lcm_gcd,
]


def generate_math_claim(is_control: bool = False) -> Claim:
    """Generate a single math claim. If is_control=True, claim_text states the TRUE fact."""
    gen = random.choice(_GENERATORS)
    claim = gen()

    if is_control:
        # Flip: claim_text presents the true statement
        true_text = claim.metadata.get("true_statement", f"The answer is {claim.ground_truth}.")
        claim = Claim(
            claim_text=true_text,
            ground_truth=claim.ground_truth,
            false_value=claim.false_value,
            category=claim.category,
            subcategory=claim.subcategory,
            is_control=True,
            metadata=claim.metadata,
        )

    return claim


def generate_math_claim_batch(n: int, control_ratio: float = 0.3) -> list[Claim]:
    """Generate n math claims with the specified control ratio."""
    n_controls = int(n * control_ratio)
    claims = []
    for i in range(n):
        is_control = i < n_controls
        claims.append(generate_math_claim(is_control=is_control))
    random.shuffle(claims)
    return claims
