from enum import Enum, auto


class PlayerMove(Enum):
    HIT = auto()
    STAY = auto()
    DOUBLE = auto()
    SPLIT = auto()
    SURRENDER = auto()
