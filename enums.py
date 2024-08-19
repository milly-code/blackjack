from enum import Enum, auto


class PlayerMove(Enum):
    HIT = auto()
    STAND = auto()
    DOUBLE = auto()
    SPLIT = auto()
    SURRENDER = auto()
