"""Logic claim generator — formal syllogisms and logical patterns."""

import random
from probe.claims.math_claims import Claim


# (A, B, X) triples: All A are B. X is a A. Therefore X is a B.
# Carefully vetted — no edge cases where the syllogism is invalid.
SYLLOGISM_TRIPLES = [
    # Biology
    ("mammals", "animals", "dogs"),
    ("mammals", "animals", "whales"),
    ("mammals", "animals", "bats"),
    ("mammals", "animals", "dolphins"),
    ("birds", "animals", "eagles"),
    ("birds", "animals", "penguins"),
    ("reptiles", "animals", "snakes"),
    ("reptiles", "animals", "crocodiles"),
    ("insects", "invertebrates", "beetles"),
    ("insects", "invertebrates", "butterflies"),
    ("fish", "vertebrates", "salmon"),
    ("amphibians", "vertebrates", "frogs"),
    # Geometry
    ("squares", "rectangles", "chess boards"),
    ("squares", "quadrilaterals", "stop signs"),
    ("rectangles", "parallelograms", "doors"),
    ("equilateral triangles", "isosceles triangles", "yield signs"),
    ("circles", "closed curves", "clock faces"),
    ("rhombuses", "parallelograms", "diamond shapes"),
    # Mathematics
    ("multiples of 10", "multiples of 5", "100"),
    ("multiples of 6", "multiples of 3", "18"),
    ("multiples of 6", "even numbers", "24"),
    ("powers of 2", "even numbers", "16"),
    ("perfect squares", "integers", "25"),
    ("prime numbers greater than 2", "odd numbers", "7"),
    ("prime numbers greater than 2", "odd numbers", "13"),
    ("prime numbers greater than 2", "odd numbers", "17"),
    # Materials
    ("metals", "conductors", "copper"),
    ("metals", "conductors", "iron"),
    ("metals", "conductors", "gold"),
    ("diamonds", "minerals", "gemstones"),
    ("rubies", "minerals", "gemstones"),
    # Geography / Social
    ("planets in the solar system", "celestial bodies", "Mars"),
    ("planets in the solar system", "celestial bodies", "Jupiter"),
    ("continents", "large landmasses", "Africa"),
    ("continents", "large landmasses", "Asia"),
    ("EU member states", "European countries", "France"),
    ("EU member states", "European countries", "Germany"),
    # Food
    ("fruits", "plants", "apples"),
    ("fruits", "plants", "bananas"),
    ("vegetables", "plants", "carrots"),
    ("grains", "plants", "wheat"),
    # Technology
    ("programming languages", "formal languages", "Python"),
    ("programming languages", "formal languages", "Java"),
    ("relational databases", "databases", "PostgreSQL"),
]

# Modus ponens: If P then Q. P. Therefore Q.
MODUS_PONENS_TEMPLATES = [
    ("it rains", "the ground gets wet", "it is raining"),
    ("it freezes", "water turns to ice", "the temperature drops below 0°C"),
    ("a number is divisible by 4", "it is divisible by 2", "16 is divisible by 4"),
    ("a shape is a square", "it has four equal sides", "this shape is a square"),
    ("an animal is a mammal", "it is warm-blooded", "a dog is a mammal"),
    ("a file is deleted", "it is no longer on disk", "this file has been deleted"),
    ("a triangle has a right angle", "it is a right triangle", "this triangle has a 90° angle"),
    ("a number is prime and greater than 2", "it is odd", "7 is prime and greater than 2"),
]

# Modus tollens: If P then Q. Not Q. Therefore not P.
MODUS_TOLLENS_TEMPLATES = [
    ("it rains", "the ground gets wet", "the ground is not wet"),
    ("an animal is a mammal", "it is warm-blooded", "this animal is not warm-blooded"),
    ("a shape is a square", "it has four sides", "this shape does not have four sides"),
    ("a number is even", "it is divisible by 2", "this number is not divisible by 2"),
    ("a circuit is complete", "current flows", "no current is flowing"),
]

# Disjunctive syllogism: Either P or Q. Not P. Therefore Q.
DISJUNCTIVE_TEMPLATES = [
    ("the switch is on", "the switch is off", "the switch is not on"),
    ("the file is in folder A", "the file is in folder B", "the file is not in folder A"),
    ("the number is positive", "the number is negative or zero", "the number is not positive"),
    ("today is a weekday", "today is a weekend", "today is not a weekday"),
]


def _categorical_syllogism() -> Claim:
    A, B, X = random.choice(SYLLOGISM_TRIPLES)
    true_conclusion = f"{X} are {B}" if X[-1] == "s" else f"{X} is a {B}"
    false_conclusion = f"{X} are not {B}" if X[-1] == "s" else f"{X} is not a {B}"

    premise = f"All {A} are {B}. {X} are {A}." if X[-1] == "s" else f"All {A} are {B}. {X} is a {A}."

    false_stmt = f"{premise} Therefore, {false_conclusion}."
    true_stmt = f"{premise} Therefore, {true_conclusion}."

    return Claim(
        claim_text=false_stmt,
        ground_truth=true_conclusion,
        false_value=false_conclusion,
        category="logic",
        subcategory="categorical_syllogism",
        metadata={"true_statement": true_stmt},
    )


def _modus_ponens() -> Claim:
    P, Q, p_instance = random.choice(MODUS_PONENS_TEMPLATES)
    true_conclusion = Q
    false_conclusion = f"not necessarily that {Q}"

    premise = f"If {P}, then {Q}. {p_instance.capitalize()}."
    false_stmt = f"{premise} Therefore, it does not necessarily follow that {Q}."
    true_stmt = f"{premise} Therefore, {Q}."

    return Claim(
        claim_text=false_stmt,
        ground_truth=true_conclusion,
        false_value=false_conclusion,
        category="logic",
        subcategory="modus_ponens",
        metadata={"true_statement": true_stmt},
    )


def _modus_tollens() -> Claim:
    P, Q, not_q = random.choice(MODUS_TOLLENS_TEMPLATES)
    true_conclusion = f"it is not the case that {P}"
    false_conclusion = f"it is still possible that {P}"

    premise = f"If {P}, then {Q}. {not_q.capitalize()}."
    false_stmt = f"{premise} Therefore, it is still possible that {P}."
    true_stmt = f"{premise} Therefore, it is not the case that {P}."

    return Claim(
        claim_text=false_stmt,
        ground_truth=true_conclusion,
        false_value=false_conclusion,
        category="logic",
        subcategory="modus_tollens",
        metadata={"true_statement": true_stmt},
    )


def _disjunctive_syllogism() -> Claim:
    P, Q, not_p = random.choice(DISJUNCTIVE_TEMPLATES)
    true_conclusion = Q
    false_conclusion = f"either {P} or {Q} could be true"

    premise = f"Either {P} or {Q}. {not_p.capitalize()}."
    false_stmt = f"{premise} Therefore, either {P} or {Q} could still be true."
    true_stmt = f"{premise} Therefore, {Q}."

    return Claim(
        claim_text=false_stmt,
        ground_truth=true_conclusion,
        false_value=false_conclusion,
        category="logic",
        subcategory="disjunctive_syllogism",
        metadata={"true_statement": true_stmt},
    )


def _logical_equivalence() -> Claim:
    equivalences = [
        ("P and Q", "Q and P", "commutativity of AND"),
        ("not (not P)", "P", "double negation"),
        ("not (P and Q)", "not P or not Q", "De Morgan's law"),
        ("not (P or Q)", "not P and not Q", "De Morgan's law"),
        ("P implies Q", "not P or Q", "material implication"),
        ("(P and Q) and R", "P and (Q and R)", "associativity of AND"),
    ]
    p_form, q_form, law = random.choice(equivalences)

    true_stmt = f"'{p_form}' is logically equivalent to '{q_form}' (by {law})."
    false_stmt = f"'{p_form}' is NOT logically equivalent to '{q_form}'."

    return Claim(
        claim_text=false_stmt,
        ground_truth=f"equivalent: {q_form}",
        false_value="not equivalent",
        category="logic",
        subcategory="logical_equivalence",
        metadata={"true_statement": true_stmt, "law": law},
    )


_GENERATORS = [
    _categorical_syllogism,
    _categorical_syllogism,  # weighted higher
    _categorical_syllogism,
    _modus_ponens,
    _modus_ponens,
    _modus_tollens,
    _disjunctive_syllogism,
    _logical_equivalence,
]


def generate_logic_claim(is_control: bool = False) -> Claim:
    gen = random.choice(_GENERATORS)
    claim = gen()

    if is_control:
        true_text = claim.metadata.get("true_statement", f"The correct conclusion is: {claim.ground_truth}.")
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


def generate_logic_claim_batch(n: int, control_ratio: float = 0.3) -> list[Claim]:
    n_controls = int(n * control_ratio)
    claims = []
    for i in range(n):
        is_control = i < n_controls
        claims.append(generate_logic_claim(is_control=is_control))
    random.shuffle(claims)
    return claims
