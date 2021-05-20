class SpecialType:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return self.name

    __str__ = __repr__


# Classes
MISSING = SpecialType("MISSING")

# Characters
ZWS = "\u200B"
ARROW_LEFT = "←"
ARROW_RIGHT = "→"

# Emoji Lists
NUMBER_EMOJIS = [
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣",
    "5️⃣",
    "6️⃣",
    "7️⃣",
    "8️⃣",
    "9️⃣",
    "🔟",
]
