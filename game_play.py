import os
import math
from models import Player, Dealer, PlayerMove, Hand
from config import INTERACTIVE, Colors, MAX_GAMES, EXPORT_FILE

from util import get_player_move, print_table

if INTERACTIVE:
    MAX_GAMES = 20


class Blackjack:
    def __init__(self):
        self.player = Player("Player 1")
        self.dealer = Dealer()
        self.game = 0
        self.results = {}
        self.hands_played = 0
        self.running_count = 0

    @staticmethod
    def log(message: str, color: str = Colors.BLUE):
        if INTERACTIVE:
            print(f"{color}{message}")
            with open("./log.txt", "a+", encoding="utf-8") as logger:
                logger.write(message)
                logger.write("\n")

    def run(self):
        while self.game < MAX_GAMES:
            self.__play()
            self.running_count = 0
            self.hands_played = 0
            self.dealer.shuffle()
        print_table(self.results, self.game)

    def __play(self):
        while not self.dealer.deck.should_create_new_deck():
            self.game += 1
            self.dealer.start_new_game(self.player)
            self.hands_played += 2  # 2 hands played each time a new game starts
            if self.player.hand(0).has_ace and self.player.hand(0).has_pairs:
                self.hands_played += 1
                self.handle_ace_split()
            elif self.player.blackjack or self.dealer.blackjack:
                self.log("Blackjack! - Someone has a blackjack")
                self.player.set_move(0, PlayerMove.STAY)
            # !Checking if player surrendered
            elif self.player_surrendered():
                self.log("Surrender - Player loses 0.5 points")
                self.player.set_move(0, PlayerMove.SURRENDER)
            else:
                player_move = get_player_move(
                    player_hand=self.player.hand(0),
                    dealer_card=self.dealer.show_card,
                    true_count=self.get_true_count(),
                    can_split=True
                )
                self.player.set_move(0, player_move)
                if self.player.last_move == PlayerMove.DOUBLE:
                    self.log("Double Down - Player receives maximum 1 card")
                    self.dealer.deal(self.player, 0)
                elif self.player.last_move == PlayerMove.HIT:
                    while self.player.last_move == PlayerMove.HIT:
                        self.log("Hit - Player receives another card")
                        self.dealer.deal(self.player, 0)
                        if self.player.charlie(0):
                            self.log("Player has a charlie - player wins")
                            break
                        player_move = get_player_move(
                            player_hand=self.player.hand(0),
                            dealer_card=self.dealer.show_card,
                            true_count=self.get_true_count(),
                            can_split=False
                        )
                        self.player.set_move(0, player_move)
                elif self.player.last_move == PlayerMove.SPLIT:
                    self.hands_played += 1
                    self.log("Split - Player hand splits")
                    self.handle_player_split()

            previous_count = self.running_count
            self.log("----------------------------------------")
            self.running_count = self.running_count + self.resolve_game()
            self.log("----------------------------------------")
            self.log(f"Previous Count {previous_count}")
            self.log(f"Running Count {self.running_count}")
            self.log(f"Hands Played {self.hands_played}")
            self.log(f"True Count {self.get_true_count()}")
            self.log(f"Deck {math.ceil(len(self.dealer.deck.cards) / 52)}")
            self.log("----------------------------------------")
            if INTERACTIVE:
                # input("Press Enter to continue... >>> ")
                if os.name == 'nt':
                    os.system('cls')
                else:
                    os.system('clear')

    def get_true_count(self):
        num_decks_remaining = math.ceil(len(self.dealer.deck.cards) / 52)
        if num_decks_remaining == 0 or self.game == 1:
            return 0
        return self.running_count / num_decks_remaining

    def handle_player_split(self):
        for hand_id in range(len(self.player.hands)):
            self.dealer.deal(self.player, hand_id)
            while True:
                player_move = get_player_move(
                    player_hand=self.player.hand(hand_id),
                    dealer_card=self.dealer.show_card,
                    true_count=self.get_true_count()
                )
                self.log(f"Player hand {player_move.name.lower()} split")
                self.player.set_move(hand_id, player_move)

                if player_move in (PlayerMove.STAY, PlayerMove.SURRENDER):
                    self.log(
                        "Surrender - Player loses 0.5 points"
                        if player_move == PlayerMove.SURRENDER
                        else "Player Stand."
                    )
                    break

                self.dealer.deal(self.player, hand_id)
                if player_move == PlayerMove.DOUBLE:
                    self.log("Double Down - Player receives maximum 1 card")
                    break

    def player_surrendered(self):
        if self.player.hand(0).has_pairs or self.player.hand(0).has_ace:
            return False

        surrendered = (
                (self.player.hand(0) == 16 and self.dealer.show_card == 10) or
                (self.player.hand(0) == 16 and self.dealer.show_card >= 9) or
                (self.player.hand(0) == 15 and self.dealer.show_card == 10)
        )
        return surrendered

    def handle_ace_split(self):
        self.log("Ace split")
        self.player.set_move(0, PlayerMove.SPLIT)
        self.player.split()
        self.dealer.deal(self.player, 0)
        self.dealer.deal(self.player, 1)

    def is_player_busted(self):
        for hand in self.player.hands:
            if not hand.is_busted:
                return False
        return True

    def all_player_hands_surrendered(self):
        for hand in self.player.hands:
            if not hand.surrendered:
                return False
        return True

    def dealer_move(self):
        self.log("Moving for dealer")
        dealer_take_cards = (
                not self.is_player_busted() and
                not self.all_player_hands_surrendered() and
                not self.player.blackjack and
                not self.dealer.blackjack
        )

        if dealer_take_cards:
            while self.dealer.hand_total < 17:
                self.log("Taking cards for dealer")
                self.dealer.deal()

    def update_results(self, key: str):
        if not INTERACTIVE:
            with open(EXPORT_FILE, "a+") as f:
                f.write(f"{key}\n")

        if self.results.get(key) is None:
            self.results[key] = 1
        else:
            self.results[key] += 1

    def get_hand_point(self, hand: Hand) -> int:
        if hand.charlie():
            return 1
        if hand == self.dealer.hand_total:
            return 0
        elif hand < self.dealer.hand_total:
            if self.dealer.is_busted:
                if hand.double_down:
                    return 2
                else:
                    return 1
            else:
                if hand.double_down:
                    return -2
                else:
                    return -1
        elif hand > self.dealer.hand_total:
            if hand.double_down:
                return 2
            else:
                return 1

    def resolve_game(self):
        card_count = 0

        self.dealer_move()
        self.log(f"Dealer Hand: \n\t {self.dealer.hand}")
        card_count = card_count + sum([card.count for card in self.dealer.hand.cards])
        self.log("Player hands: ")
        for hand in self.player.hands:
            self.log(f"\t {hand}")
            card_count = card_count + sum([card.count for card in hand.cards])

        if self.player.blackjack or self.dealer.blackjack:
            if self.player.blackjack and self.dealer.blackjack:
                self.log("Push - Player Points = 0", Colors.WARNING)
                self.update_results("0")
            elif self.dealer.blackjack:
                self.log("Dealer wins - Player Points = -1", Colors.FAIL)
                self.update_results("-1")
            else:
                self.log("Player wins - Player Points = +1.5", Colors.GREEN)
                self.update_results("1.5")
        elif len(self.player.hands) == 1:
            hand = self.player.hand(0)

            _hand = Hand([hand.cards[0], hand.cards[1]])

            if hand.has_ace and _hand.total == 14 and self.dealer.hand.cards[0].value == 6 \
                    and self.dealer.hand_total != hand.total:
                if self.dealer.hand_total > hand.total:
                    self.log("Player loses -2 points", Colors.FAIL)
                    self.update_results("-2")
                else:
                    self.log("Player Wins +1 point", Colors.GREEN)
                    self.update_results("2")
            elif hand.charlie():
                self.log("Charlie - Player wins +1 point", Colors.GREEN)
                self.update_results("1")
            elif hand.is_busted:
                if hand.double_down:
                    self.log("Busted - Player loses -2 point", Colors.FAIL)
                    self.update_results("-2")
                else:
                    self.log("Busted - Player loses -1 point", Colors.FAIL)
                    self.update_results("-1")
            elif hand.surrendered:
                self.log("Surrender - Player loses -0.5 points", Colors.FAIL)
                self.update_results("-0.5")
            elif self.dealer.is_busted:
                if hand.double_down:
                    self.log("Dealer busted - Player wins +2 point", Colors.GREEN)
                    self.update_results("2")
                else:
                    self.log("Dealer busted - Player wins +1 point", Colors.GREEN)
                    self.update_results("1")
            elif hand == self.dealer.hand_total:
                self.log("Push - Player draws (0 points)", Colors.WARNING)
                self.update_results("0")
            elif hand < self.dealer.hand_total:
                if hand.double_down:
                    self.log("Double Down - Player loses -2 points", Colors.FAIL)
                    self.update_results("-2")
                else:
                    self.log("Dealer wins - Player loses -1 point", Colors.FAIL)
                    self.update_results("-1")
            elif hand > self.dealer.hand_total:
                if hand.double_down:
                    self.log("Double Down - Player wins +2 points", Colors.GREEN)
                    self.update_results("2")
                else:
                    self.log("Dealer loss - Player wins +1 point", Colors.GREEN)
                    self.update_results("1")
            else:
                self.log("Should never happen", Colors.FAIL)
                raise Exception("Should never happen")
        else:
            # player has 2 hands
            if all(hand.is_busted for hand in self.player.hands):
                # both hands busted then we subtract 2 points
                self.log("Split hands Busted - Player loses -2 points", Colors.FAIL)
                self.update_results("-2")
            elif any(hand.is_busted for hand in self.player.hands):
                # one hand busted then we subtract at least 1 point
                point = -1
                for hand in self.player.hands:
                    if not hand.is_busted:
                        point = point + self.get_hand_point(hand)
                self.log(f"Player {point} points", Colors.FAIL)
                self.update_results(str(point))
            else:
                point = sum(
                    [self.get_hand_point(self.player.hand(0)),
                     self.get_hand_point(self.player.hand(1))]
                )
                self.log(
                    f"Player {point} points",
                    Colors.FAIL if point < 0 else
                    (Colors.WARNING if point == 0 else Colors.GREEN)
                )
                self.update_results(str(point))

        return card_count


if __name__ == '__main__':
    try:
        open(EXPORT_FILE, 'w').close()
        open("./log.txt", "w").close()
        for _ in range(1):
            bj = Blackjack()
            bj.run()
            print(" ")
    except KeyboardInterrupt:
        print("Exiting...")
        exit()
