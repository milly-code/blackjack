import string
from typing import List, Optional
from random import shuffle, choices
from config import *
from enums import PlayerMove
import warnings


class PlayingCard:
    def __init__(self, name: str, suit: str, count: int = 0):
        self.name = name
        self.suit = suit
        self.count = count
        self.value = self._determine_value()

    def _determine_value(self) -> int:
        if self.name == 'A':
            return 11
        elif self.name in {'J', 'Q', 'K'}:
            return 10
        else:
            return int(self.name)

    def __repr__(self) -> str:
        return f'PlayingCard(value={self.name}, suite={self.suit}, count={self.count})'

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other) -> bool:
        if isinstance(other, PlayingCard):
            return (self.name, self.suit, self.value) == (other.name, other.suit, other.value)
        if isinstance(other, int):
            return self.value == other
        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, PlayingCard):
            return self.name == other.name and self.suit == other.suit and self.value == other.value
        if isinstance(other, int):
            return self.value >= other
        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, PlayingCard):
            return self.name > other.name and self.suit > other.suit and self.value > other.value
        if isinstance(other, int):
            return self.value > other
        return False

    def __le__(self, other) -> bool:
        if isinstance(other, PlayingCard):
            return self.name <= other.name and self.suit <= other.suit and self.value <= other.value
        if isinstance(other, int):
            return self.value <= other
        return False

    def copy(self, suit=None):
        return PlayingCard(self.name, suit or self.suit)


class PlayingCardDeck:
    def __init__(self):
        self.cards = []
        self.shuffle()

    def create_card_pack(self):
        for data in card_values:
            face, count = data
            for suit in SUITS:
                self.cards.append(PlayingCard(face, suit, count=count))

    def shuffle(self):
        self.cards = []
        for _ in range(MAX_DECK_PER_SERIES):
            self.create_card_pack()
        shuffle(self.cards)

    def should_create_new_deck(self) -> bool:
        total_cards_dealt = (CARD_COUNT_PER_DECK * MAX_DECK_PER_SERIES) - len(self.cards)
        return total_cards_dealt >= MAX_CARDS_PER_SERIES

    def deal(self) -> PlayingCard:
        return self.cards.pop(0)


class Hand:
    def __init__(self, cards: Optional[List[PlayingCard]] = None, is_dealer=True):
        self.cards: List[PlayingCard] = cards or []  # cards
        self.moves: List[PlayerMove] = []
        self.is_dealer = is_dealer

    def add_cards(self, cards: List[PlayingCard]):
        self.cards.extend(cards)
        return self

    def add_card(self, card: PlayingCard):
        self.cards.append(card)
        return self

    def charlie(self):
        return len(self.cards) == 7 and self.total <= 21

    @property
    def has_ace(self) -> bool:
        return any(card.name == 'A' for card in self.cards)

    @property
    def is_blackjack(self) -> bool:
        return self.total == 21 and len(self.cards) == 2

    @property
    def is_busted(self) -> bool:
        return self.total > 21

    @property
    def has_pairs(self) -> bool:
        return len(self.cards) == 2 and self.cards[0].value == self.cards[1].value

    @property
    def total(self) -> int:
        total = sum(card.value for card in self.cards)
        num_aces = sum(1 for card in self.cards if card.name == 'A')
        while total > 21 and num_aces:
            total -= 10
            num_aces -= 1
        return total

    @property
    def is_flush(self) -> bool:
        suits = set(card.suit for card in self.cards)
        return len(suits) == 1

    @property
    def real_value(self) -> int:
        raise Exception("func `real_value` is no longer valid")
        # return sum(card.value for card in self.cards)

    @property
    def can_double_down(self):
        return self.last_move != PlayerMove.DOUBLE and len(self) == 2

    @property
    def last_move(self):
        return self.moves[-1] if self.moves else None

    @property
    def double(self):
        warnings.warn(
            "Use `double_down` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return PlayerMove.DOUBLE in self.moves

    @property
    def double_down(self):
        return PlayerMove.DOUBLE in self.moves

    @property
    def surrendered(self):
        return self.last_move == PlayerMove.SURRENDER

    def __eq__(self, other):
        if isinstance(other, Hand):
            return self.total == other.total
        elif isinstance(other, int):
            return self.total == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, Hand):
            return self.total < other.total
        elif isinstance(other, int):
            return self.total < other
        return False

    def __le__(self, other):
        if isinstance(other, Hand):
            return self.total <= other.total
        elif isinstance(other, int):
            return self.total <= other
        return False

    def __gt__(self, other):
        if isinstance(other, Hand):
            return self.total > other.total
        elif isinstance(other, int):
            return self.total > other
        return False

    def __ge__(self, other):
        if isinstance(other, Hand):
            return self.total >= other.total
        elif isinstance(other, int):
            return self.total >= other
        return False

    def __repr__(self):
        card_sum = sum([card.count for card in self.cards])
        if self.is_dealer:
            return f"<Hand(cards={self.cards}, total={self.total}, count={card_sum})/>"
        v = 'soft-hand' if self.has_usable_ace() else 'hard-hand'
        return f"<Hand(cards={self.cards}, total={self.total}, type={v}, count={card_sum}) />"

    def has_usable_ace(self):
        if not self.has_ace:
            # if no ace in hand then no usable ace
            return False
        total = sum(card.value for card in self.cards)
        num_aces = sum(1 for card in self.cards if card.name == 'A')
        while total > 21 and num_aces:
            total -= 10
            num_aces -= 1
        return num_aces > 0

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return len(self.cards)


class Player:
    def __init__(self, name: string):
        self._id = "player_" + ''.join(choices(string.ascii_lowercase + string.digits, k=15))
        self.hands: List[Hand] = [Hand()]
        self.name = name

    def set_move(self, hand_id: int, move: PlayerMove) -> 'Player':
        self.hand(hand_id).moves.append(move)
        if move == PlayerMove.SPLIT:
            self.split()
        return self

    def split(self) -> 'Player':
        if len(self.hands) == 2:
            # cannot split if split before
            return self
        if len(self.hands[0].cards) > 2:
            # cannot split if not enough cards
            return self
        card = self.hands[0].cards.pop(0)
        hand = Hand([card])
        hand.moves.append(PlayerMove.SPLIT)
        self.hands.append(hand)
        return self

    def reset(self) -> 'Player':
        self.hands = [Hand(is_dealer=False)]
        return self

    @property
    def last_move(self) -> PlayerMove:
        return self.hands[-1].last_move

    def add_card(self, card: PlayingCard, hand_id=0) -> 'Player':
        # can only split once. player should only have max 2 hands
        hand_id = min(1, abs(hand_id))
        self.hand(hand_id).add_card(card)
        return self

    def add_cards(self, cards: List[PlayingCard], hand_id=0) -> 'Player':
        self.hands[hand_id].add_cards(cards)
        return self

    def hand(self, _id: int) -> Hand:
        return self.hands[_id]

    def charlie(self, hand_id: int = 0) -> bool:
        return self.hand(hand_id).charlie()

    def __str__(self):
        return f"<Player: {self._id} | {self.name} | {self.hands}/>"

    def __repr__(self):
        return self.__str__()

    @property
    def blackjack(self) -> bool:
        return len(self.hands) == 1 and self.hand(0).is_blackjack


class Dealer(object):
    def __init__(self):
        self._id = "dealer_" + ''.join(choices(string.ascii_lowercase + string.digits, k=15))
        self.hand: Hand = Hand()
        self.__deck__ = PlayingCardDeck()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Dealer, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    @property
    def dealer_second_card(self):
        return self.hand.cards[1]

    @property
    def show_card(self):
        return self.hand.cards[0]

    @property
    def is_busted(self):
        return self.hand.is_busted

    def add_card(self, card: PlayingCard):
        self.hand.add_card(card)
        return self

    def add_cards(self, cards: List[PlayingCard]):
        self.hand.add_cards(cards)
        return self

    def should_create_new_deck(self) -> bool:
        return self.deck.should_create_new_deck()

    def shuffle(self) -> 'Dealer':
        self.deck.shuffle()
        return self

    @property
    def hand_total(self) -> int:
        return self.hand.total

    @property
    def deck(self):
        return self.__deck__

    @deck.setter
    def deck(self, value):
        raise ValueError("Cannot set deck: " + str(value))

    def deal(self, player: Optional[Player] = None, player_hand_id=0) -> int:
        card = self.deck.deal()
        if player:
            player.add_card(card, player_hand_id)
        else:
            self.add_card(self.deck.deal())
        return card.count

    def reset(self):
        self.hand = Hand(is_dealer=True)
        return self

    def start_new_game(self, player: Player) -> int:
        player.reset()
        self.reset()

        count = (
            self.deal()
            + self.deal(player, 0)
            + self.deal()
            + self.deal(player, 0)
        )
        return count

    def __str__(self):
        return f"<Dealer: {self._id} | {self.hand}/>"

    def __repr__(self):
        return self.__str__()

    @property
    def blackjack(self) -> bool:
        return self.hand.total == 21 and len(self.hand.cards) == 2


__all__ = ['Dealer', 'PlayerMove', 'Player', 'Hand', 'PlayingCard', 'PlayingCardDeck']
