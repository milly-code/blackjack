from typing import Any
from config import INTERACTIVE, Colors, MAX_GAMES, EXPORT_FILE
from models import Player, Dealer, PlayerMove, Hand
from util import get_player_move, get_hand_value


class Logger:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'

    def __init__(self, file_path="./log.txt"):
        self.__file_path = file_path

    def __call__(self, *args: Any):
        self.log(*args)

    def log(self, message: str, color='\033[94m'):
        if INTERACTIVE:
            print(f"{color}{message}")

        with open(self.__file_path, "a+", encoding="utf-8") as logger:
            logger.write(message)
            logger.write("\n")

    def clear(self):
        open(self.__file_path, "w").close()

    def success(self, message: str):
        self.log(message=message, color=Colors.GREEN)

    def fail(self, message: str):
        self.log(message=message, color=Colors.FAIL)

    def warn(self, message: str):
        self.log(message=message, color=Colors.WARNING)


class Blackjack:
    def __init__(self) -> None:
        self.results = {}
        self.player = Player("Player 1")
        self.dealer = Dealer()

        self.total_games = 0
        self.hands_played = 0
        self.running_count = 0

        self.logger = Logger()

    def reset(self):
        self.total_games = 0
        self.hands_played = 0
        self.running_count = 0
        self.dealer.shuffle()

    def __call__(self) -> Any:
        while self.total_games < MAX_GAMES:
            self.run()
            self.reset()

    def blackjack_winner(self, p=True):
        if self.dealer.blackjack and not self.player.blackjack:
            points = "-0.5" if self.player.has_insurance else "-1"
        elif self.player.blackjack and not self.dealer.blackjack:
            points = "1" if self.player.has_insurance else "1.5"
        elif self.dealer.blackjack and self.player.blackjack:
            points = "0" if self.player.has_insurance else "0.5"
        else:
            self.logger.fail(f"{self.dealer}")
            self.logger.fail(f"{self.player}")
            raise ValueError("No one BLACKJACK. Should not happen")

        if p:
            name = 'Both ' if self.dealer.blackjack \
                and self.player.blackjack else 'Dealer ' \
                if self.dealer.blackjack else 'Player '
            self.logger(f"{name}BLACKJACK | Points = {points}")
        return points

    def update_results(self, key: str):
        if not INTERACTIVE:
            with open(EXPORT_FILE, 'a+') as f:
                f.write(f"{key}\n")

        if self.results.get(key) is None:
            self.results[key] = 1
        else:
            self.results[key] += 1

    @property
    def true_count(self) -> float:
        num_decks_remaining = get_hand_value(self.hands_played)
        if num_decks_remaining == 0 or self.total_games == 1:
            return 0.0
        return self.running_count / num_decks_remaining

    def get_player_cards(self):
        player_move = get_player_move(
            player_hand=self.player.hand(0),
            dealer_card=self.dealer.show_card,
            true_count=self.true_count,
            can_split=True
        )

        self.player.set_move(hand_id=0, move=player_move)

        if player_move == PlayerMove.DOUBLE:
            # player can only take one extra card
            self.dealer.deal(player=self.player, player_hand_id=0)
        elif player_move == PlayerMove.HIT:
            # Hit until either bust or STAND
            self.logger("Player decided to hit")
            while player_move == PlayerMove.HIT:
                self.dealer.deal(player=self.player, player_hand_id=0)
                if self.player.charlie(0):
                    self.logger("Player has 7 cards. Player CHARLIE!")
                    break
                player_move = get_player_move(
                    player_hand=self.player.hand(0),
                    dealer_card=self.dealer.show_card,
                    true_count=self.true_count,
                    can_split=False
                )
                self.player.set_move(hand_id=0, move=player_move)
        elif player_move == PlayerMove.SPLIT:
            self.hands_played += 1
            self.logger("Player decided to split")
            for hand_id in range(len(self.player.hands)):
                self.dealer.deal(player=self.player,
                                 player_hand_id=hand_id)

                while True:
                    player_move = get_player_move(
                        player_hand=self.player.hand(hand_id),
                        dealer_card=self.dealer.show_card,
                        true_count=self.true_count,
                        can_split=False
                    )
                    self.player.set_move(hand_id, player_move)

                    if player_move in (PlayerMove.STAND, PlayerMove.SURRENDER):
                        break

                    self.dealer.deal(self.player, hand_id)
                    if player_move == PlayerMove.DOUBLE:
                        break
        elif player_move == PlayerMove.STAND:
            self.logger("Player decided to stand")

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

    def get_dealer_cards(self):
        self.logger("Dealer Taking Cards")

        dealer_take_cards = (
            not self.is_player_busted()
            and not self.all_player_hands_surrendered()
            and not self.player.blackjack
            and not self.dealer.blackjack
        )

        while dealer_take_cards and self.dealer.hand_total < 17:
            self.dealer.deal()

    def resolve_game(self):
        if self.is_player_surrendered():
            self.update_results("0.5")
        elif self.player.blackjack or self.dealer.blackjack:
            self.update_results(self.blackjack_winner(p=False))
        elif all(h.is_busted for h in self.player.hands):
            # don't take card for dealer if player hands are busted
            pass
        else:
            self.get_dealer_cards()
        self.print_hands()

        card_count = sum([c.count for c in self.dealer.hand.cards])
        card_count += self.player.card_count

        if len(self.player.hands) == 1:
            hand = self.player.hand(0)

            if hand.has_ace and hand.total == 14 \
                    and self.dealer.show_card == 6 \
                    and self.dealer.hand_total != hand.total:
                if self.dealer.hand > hand and not self.dealer.hand.is_busted:
                    self.logger("Player lost | Points = -2")
                    self.update_results("-2")
                else:
                    self.logger("Player won | Points = 2")
                    self.update_results("2")
            elif hand.charlie():
                self.logger("Player has 7 cards | Charlie! | Point = 1")
                self.update_results("1")
            elif self.dealer.hand.is_busted and not hand.is_busted:
                if hand.double_down:
                    self.logger("Player won | Double Down | Points = 2")
                    self.update_results("2")
                else:
                    self.logger("Player won | Point = 1")
                    self.update_results("1")
            elif hand.is_busted:
                if hand.double_down:
                    self.logger(
                        "Player hand Busted | Double Down | Point = -2")
                    self.update_results("-2")
                else:
                    self.logger("Player hand Busted | Point = -1")
                    self.update_results("-1")
            elif hand == self.dealer.hand_total:
                self.logger("Draw result | Point = 0")
                self.update_results("0")
            elif hand < self.dealer.hand:
                if hand.double_down:
                    self.logger("Player lost | Double Down | Points = -2")
                    self.update_results("-2")
                else:
                    self.logger("Player lost | Point = -1")
                    self.update_results("-1")
            elif hand > self.dealer.hand:
                if hand.double_down:
                    self.logger("Player won | Double Down | Points = 2")
                    self.update_results("2")
                else:
                    self.logger("Player won | Point = 1")
                    self.update_results("1")
            else:
                raise ValueError("Should never happen")
        else:
            if all(h.is_busted for h in self.player.hands):
                self.logger("Player lost | Split Hands | Points = -2")
                self.update_results("-2")
            elif any(h.is_busted for h in self.player.hands):
                point = -1
                count = len(self.player.hands)
                for h in self.player.hands:
                    if not h.is_busted:
                        point += self.get_hand_point(h)
                        count -= 1

                self.logger(f"Player lost {count}/{len(self.player.hands)} | Points = {point}")
                self.update_results(str(point))
            else:
                point = sum([self.get_hand_point(h) for h in self.player.hands])
                name = 'lost' if point < 0 else 'won' if point > 0 else 'pushed'
                self.logger(f"Player {name} | Points = {point}")
                self.update_results(str(point))

        return card_count

    def take_insurance_play(self):
        # must check if player also blackjack
        self.player.has_insurance = True
        if self.dealer.blackjack or self.player.blackjack:
            self.blackjack_winner()
        else:
            self.logger("No BLACKJACK for Dealer. Player lost insurance")
            self.get_player_cards()
            self.resolve_game()

    def is_player_surrendered(self):
        if self.player.hand(0).has_pairs or self.player.hand(0).has_ace or len(self.player.hands) > 1:
            return False

        surrendered = (
            (self.player.hand(0) == 16 and self.dealer.show_card == 10) or
            (self.player.hand(0) == 16 and self.dealer.show_card >= 9) or
            (self.player.hand(0) == 15 and self.dealer.show_card == 10)
        )
        return surrendered

    def print_hands(self):
        self.logger(f"Dealer Hand: \n\t {self.dealer.hand}")
        self.logger("Player hands: ")
        for hand in self.player.hands:
            self.logger(f"\t {hand}")

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

    def handle_ace_split(self):
        self.player.split()
        self.dealer.deal(player=self.player, player_hand_id=0)
        self.dealer.deal(player=self.player, player_hand_id=1)
        self.hands_played += 1

    def run(self):
        self.logger.clear()
        while not self.dealer.should_shuffle(hands_played=self.hands_played):
            self.dealer.start_new_game(self.player)
            self.hands_played += 2
            self.total_games += 1

            # check if player should take insurance
            if self.dealer.show_card == 'A' and self.true_count >= 5:
                self.logger("Dealer showing ace card. Player taking insurance")
                self.take_insurance_play()
            # check if player has surrendered
            elif self.is_player_surrendered():
                self.logger("Player surrendering | Points = 0.5")
                self.player.set_move(0, PlayerMove.SURRENDER)
            # check if player or dealer has blackjack
            elif self.dealer.blackjack or self.player.blackjack:
                self.logger("We have a BLACKJACK Winner")
                self.blackjack_winner()
            elif self.player.hand(0).has_ace and self.player.hand(0).has_pairs:
                # If the player has a pair of ace
                self.logger("Player has a pair of ace. Splitting")
                self.handle_ace_split()
            else:
                # continue as normal
                self.get_player_cards()

            prev_count = self.running_count
            self.logger("----------------------------------------")
            self.running_count += self.resolve_game()
            self.logger(f"Previous Count {prev_count}")
            self.logger(f"Running Count {self.running_count}")
            self.logger(f"Hands Played {self.hands_played}")
            self.logger(f"True Count {self.true_count}")
            self.logger(f"Deck {get_hand_value(self.hands_played)}")
            self.logger("----------------------------------------")


if __name__ == '__main__':
    game = Blackjack()
    game.run()
