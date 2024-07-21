MAX_CARDS_PER_SERIES = 204
MAX_GAMES = 2_000
MAX_DECK_PER_SERIES = 6
CARD_COUNT_PER_DECK = 52
MAXIMUM_PLAYERS = 1
INTERACTIVE = True

EXPORT_FILE = 'export.txt'

Hearts = "\u2665"
Spades = "\u2660"
Diamonds = "\u2666"
Clubs = "\u2663"

SUITS = [Hearts, Spades, Diamonds, Clubs]
card_values = [('2', 1), ('3', 1), ('4', 2), ('5', 2),
               ('6', 2), ('7', 1), ('8', 0), ('9', 0),
               ('10', -2), ('J', -2), ('K', -2), ('Q', -2),
               ('A', -1)]


class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
