"""Science claim generator — hardcoded verified facts with plausible false alternatives."""

import random
from probe.claims.math_claims import Claim

# ---------------------------------------------------------------------------
# CACHED_FACTS: each entry has "question", "value" (true), "false" (plausible wrong)
# False values are hand-picked to be plausible, not random noise.
# ---------------------------------------------------------------------------

CACHED_FACTS: dict[str, list[dict]] = {
    "atomic_numbers": [
        {"q": "The atomic number of hydrogen", "value": "1", "false": "2"},
        {"q": "The atomic number of helium", "value": "2", "false": "4"},
        {"q": "The atomic number of lithium", "value": "3", "false": "6"},
        {"q": "The atomic number of carbon", "value": "6", "false": "8"},
        {"q": "The atomic number of nitrogen", "value": "7", "false": "6"},
        {"q": "The atomic number of oxygen", "value": "8", "false": "10"},
        {"q": "The atomic number of sodium", "value": "11", "false": "12"},
        {"q": "The atomic number of magnesium", "value": "12", "false": "14"},
        {"q": "The atomic number of aluminum", "value": "13", "false": "14"},
        {"q": "The atomic number of silicon", "value": "14", "false": "16"},
        {"q": "The atomic number of phosphorus", "value": "15", "false": "16"},
        {"q": "The atomic number of sulfur", "value": "16", "false": "18"},
        {"q": "The atomic number of chlorine", "value": "17", "false": "18"},
        {"q": "The atomic number of argon", "value": "18", "false": "20"},
        {"q": "The atomic number of potassium", "value": "19", "false": "18"},
        {"q": "The atomic number of calcium", "value": "20", "false": "22"},
        {"q": "The atomic number of iron", "value": "26", "false": "28"},
        {"q": "The atomic number of copper", "value": "29", "false": "28"},
        {"q": "The atomic number of zinc", "value": "30", "false": "32"},
        {"q": "The atomic number of silver", "value": "47", "false": "48"},
        {"q": "The atomic number of gold", "value": "79", "false": "78"},
        {"q": "The atomic number of mercury", "value": "80", "false": "78"},
        {"q": "The atomic number of lead", "value": "82", "false": "84"},
        {"q": "The atomic number of uranium", "value": "92", "false": "90"},
    ],
    "physical_constants": [
        {"q": "The speed of light in a vacuum", "value": "299,792 km/s", "false": "284,000 km/s"},
        {"q": "The gravitational acceleration on Earth's surface", "value": "9.81 m/s²", "false": "10.24 m/s²"},
        {"q": "The boiling point of water at standard pressure", "value": "100°C", "false": "98°C"},
        {"q": "The freezing point of water at standard pressure", "value": "0°C", "false": "-4°C"},
        {"q": "The number of bones in the adult human body", "value": "206", "false": "212"},
        {"q": "The number of chromosomes in a human cell", "value": "46", "false": "48"},
        {"q": "The pH of pure water", "value": "7", "false": "6"},
        {"q": "The normal human body temperature", "value": "37°C", "false": "38.5°C"},
        {"q": "The melting point of ice at standard pressure", "value": "0°C", "false": "-2°C"},
        {"q": "The atomic mass of carbon", "value": "12 u", "false": "14 u"},
        {"q": "The number of protons in a water molecule", "value": "10", "false": "8"},
        {"q": "The number of valence electrons in oxygen", "value": "6", "false": "4"},
        {"q": "The half-life of carbon-14", "value": "5,730 years", "false": "4,200 years"},
    ],
    "geography": [
        {"q": "The capital of Australia", "value": "Canberra", "false": "Sydney"},
        {"q": "The capital of Brazil", "value": "Brasília", "false": "Rio de Janeiro"},
        {"q": "The capital of Canada", "value": "Ottawa", "false": "Toronto"},
        {"q": "The capital of New Zealand", "value": "Wellington", "false": "Auckland"},
        {"q": "The capital of South Africa", "value": "Pretoria", "false": "Cape Town"},
        {"q": "The capital of Switzerland", "value": "Bern", "false": "Zurich"},
        {"q": "The capital of India", "value": "New Delhi", "false": "Mumbai"},
        {"q": "The capital of Japan", "value": "Tokyo", "false": "Osaka"},
        {"q": "The capital of Germany", "value": "Berlin", "false": "Munich"},
        {"q": "The capital of Spain", "value": "Madrid", "false": "Barcelona"},
        {"q": "The largest ocean on Earth", "value": "Pacific Ocean", "false": "Atlantic Ocean"},
        {"q": "The longest river in the world", "value": "Nile River", "false": "Amazon River"},
        {"q": "The highest mountain in the world", "value": "Mount Everest", "false": "K2"},
        {"q": "The largest continent by area", "value": "Asia", "false": "Africa"},
        {"q": "The largest country by area", "value": "Russia", "false": "Canada"},
        {"q": "The largest country by population", "value": "India", "false": "China"},
        {"q": "The smallest country in the world by area", "value": "Vatican City", "false": "Monaco"},
        {"q": "The deepest ocean trench", "value": "Mariana Trench", "false": "Tonga Trench"},
        {"q": "The number of continents on Earth", "value": "7", "false": "6"},
        {"q": "The number of oceans on Earth", "value": "5", "false": "4"},
    ],
    "astronomy": [
        {"q": "The number of planets in our solar system", "value": "8", "false": "9"},
        {"q": "The closest planet to the Sun", "value": "Mercury", "false": "Venus"},
        {"q": "The largest planet in our solar system", "value": "Jupiter", "false": "Saturn"},
        {"q": "The planet with the most moons", "value": "Saturn", "false": "Jupiter"},
        {"q": "The planet closest to Earth in size", "value": "Venus", "false": "Mars"},
        {"q": "The distance from Earth to the Moon (approximate)", "value": "384,400 km", "false": "420,000 km"},
        {"q": "The distance from Earth to the Sun (approximate)", "value": "150 million km", "false": "130 million km"},
        {"q": "The age of the universe (approximate)", "value": "13.8 billion years", "false": "12.5 billion years"},
        {"q": "The age of Earth (approximate)", "value": "4.5 billion years", "false": "3.8 billion years"},
        {"q": "The planet known as the Red Planet", "value": "Mars", "false": "Jupiter"},
        {"q": "The hottest planet in our solar system", "value": "Venus", "false": "Mercury"},
    ],
    "chemistry": [
        {"q": "The chemical symbol for water", "value": "H₂O", "false": "HO₂"},
        {"q": "The chemical symbol for table salt", "value": "NaCl", "false": "NaOH"},
        {"q": "The chemical symbol for carbon dioxide", "value": "CO₂", "false": "CO"},
        {"q": "The chemical symbol for ammonia", "value": "NH₃", "false": "N₂H"},
        {"q": "The chemical symbol for sulfuric acid", "value": "H₂SO₄", "false": "H₂S₂O₄"},
        {"q": "The chemical symbol for glucose", "value": "C₆H₁₂O₆", "false": "C₆H₁₀O₅"},
        {"q": "The number of hydrogen atoms in a methane molecule", "value": "4", "false": "3"},
        {"q": "The number of carbon atoms in a butane molecule", "value": "4", "false": "3"},
        {"q": "The boiling point of ethanol", "value": "78.4°C", "false": "65°C"},
        {"q": "The melting point of iron", "value": "1,538°C", "false": "1,200°C"},
    ],
    "biology": [
        {"q": "The number of chambers in a human heart", "value": "4", "false": "3"},
        {"q": "The molecule that carries genetic information in cells", "value": "DNA", "false": "RNA"},
        {"q": "The powerhouse of the cell", "value": "mitochondria", "false": "nucleus"},
        {"q": "The number of bases in the human DNA codon", "value": "3", "false": "4"},
        {"q": "The blood type considered the universal donor", "value": "O negative", "false": "AB positive"},
        {"q": "The blood type considered the universal recipient", "value": "AB positive", "false": "O positive"},
        {"q": "The largest organ in the human body", "value": "skin", "false": "liver"},
        {"q": "The longest bone in the human body", "value": "femur", "false": "tibia"},
        {"q": "The number of teeth in an adult human", "value": "32", "false": "28"},
        {"q": "The average number of heartbeats per minute at rest", "value": "72", "false": "60"},
    ],
}


def _make_claim_text(q: str, true_val: str, false_val: str) -> tuple[str, str]:
    """Return (false_claim_text, true_claim_text)."""
    false_text = f"{q} is {false_val}."
    true_text = f"{q} is {true_val}."
    return false_text, true_text


def generate_science_claim(is_control: bool = False) -> Claim:
    category = random.choice(list(CACHED_FACTS.keys()))
    fact = random.choice(CACHED_FACTS[category])

    false_text, true_text = _make_claim_text(fact["q"], fact["value"], fact["false"])

    if is_control:
        claim_text = true_text
    else:
        claim_text = false_text

    return Claim(
        claim_text=claim_text,
        ground_truth=fact["value"],
        false_value=fact["false"],
        category="science",
        subcategory=category,
        is_control=is_control,
        metadata={"question": fact["q"], "true_statement": true_text},
    )


def generate_science_claim_batch(n: int, control_ratio: float = 0.3) -> list[Claim]:
    n_controls = int(n * control_ratio)
    claims = []
    for i in range(n):
        is_control = i < n_controls
        claims.append(generate_science_claim(is_control=is_control))
    random.shuffle(claims)
    return claims
