from enums import PlayerMove
from models import Hand, PlayingCard
from typing import Union, List, Optional

USE_PRETTY_TABLE = True

try:
    # noinspection PyUnresolvedReferences
    from prettytable import PrettyTable
except ModuleNotFoundError:
    USE_PRETTY_TABLE = False


def _get_soft_play(player_hand: Hand, dealer_card: PlayingCard) -> PlayerMove:
    if player_hand == 20:
        return PlayerMove.STAY
    elif player_hand == 19:
        if dealer_card.value != 6 or not player_hand.can_double_down:
            return PlayerMove.STAY
        return PlayerMove.DOUBLE
    elif player_hand == 18:
        if dealer_card.value in [7, 8] or (not player_hand.can_double_down and dealer_card.value <= 6):
            return PlayerMove.STAY
        elif dealer_card.value <= 6:
            return PlayerMove.DOUBLE
        return PlayerMove.HIT
    elif player_hand == 17:
        if dealer_card.value in [3, 4, 5, 6]:
            return PlayerMove.DOUBLE if player_hand.can_double_down else PlayerMove.HIT
        return PlayerMove.HIT
    elif player_hand == 16 or player_hand == 15:
        if dealer_card.value in [4, 5, 6]:
            return PlayerMove.DOUBLE if player_hand.can_double_down else PlayerMove.HIT
        return PlayerMove.HIT
    elif player_hand == 13 or player_hand == 14:
        if dealer_card.value == 6 and player_hand == 14:
            return PlayerMove.DOUBLE
        if dealer_card.value in [5, 6]:
            return PlayerMove.DOUBLE if player_hand.can_double_down else PlayerMove.HIT
        return PlayerMove.HIT
    return PlayerMove.STAY


def _get_hard_play(player_hand: Hand, dealer_card: PlayingCard) -> PlayerMove:
    if player_hand < 9:
        return PlayerMove.HIT
    elif player_hand == 9:
        if dealer_card.value == 6 and player_hand.can_double_down:
            return PlayerMove.DOUBLE
        if dealer_card.value in [2, 7, 8, 9, 10, 11] or not player_hand.can_double_down:
            return PlayerMove.HIT
        return PlayerMove.DOUBLE
    elif player_hand == 10:
        if dealer_card.value in [10, 11] or not player_hand.can_double_down:
            return PlayerMove.HIT
        return PlayerMove.DOUBLE if player_hand.can_double_down else PlayerMove.HIT
    elif player_hand == 11:
        if dealer_card.value == 5:
            return PlayerMove.DOUBLE
        return PlayerMove.DOUBLE if player_hand.can_double_down else PlayerMove.HIT
    elif player_hand == 12:
        return PlayerMove.STAY if dealer_card.value in [4, 5, 6] else PlayerMove.HIT
    elif player_hand == 13 or player_hand == 14:
        return PlayerMove.STAY if dealer_card.value < 7 else PlayerMove.HIT
    elif player_hand == 15:
        return PlayerMove.STAY if dealer_card.value < 7 else PlayerMove.HIT
    elif player_hand == 16:
        return PlayerMove.STAY if dealer_card.value < 7 else PlayerMove.HIT
    return PlayerMove.STAY


def _get_pairs_play(player_hand: Hand, dealer_card: PlayingCard) -> PlayerMove:
    if player_hand.has_ace:  # Player has a pair of aces
        return PlayerMove.SPLIT
    if player_hand.total in [4, 6, 7, 14]:
        return PlayerMove.SPLIT if dealer_card.value < 8 else PlayerMove.HIT
    elif player_hand == 8:
        return PlayerMove.SPLIT if dealer_card.value in [5, 6] else PlayerMove.HIT
    elif player_hand == 10:
        return PlayerMove.DOUBLE if dealer_card.value < 10 else PlayerMove.HIT
    elif player_hand == 12:
        return PlayerMove.SPLIT if dealer_card.value < 7 else PlayerMove.HIT
    elif player_hand == 18:
        return PlayerMove.STAY if dealer_card.value in [7, 10, 11] else PlayerMove.SPLIT
    elif player_hand == 20:
        return PlayerMove.STAY
    elif player_hand == 16:
        return PlayerMove.SPLIT

    raise ValueError(f"Player hand total: {player_hand.total}")


def _get_true_count_play(player_hand: Hand, dealer_card: PlayingCard, true_count: float, ) -> Optional[PlayerMove]:
    if true_count == 0:
        return None
    if player_hand.total == 16 and dealer_card.value == 9 and true_count >= 8:
        return PlayerMove.STAY
    elif (player_hand.total == 20 and player_hand.has_pairs
          and (dealer_card.value == 5 or dealer_card.value == 6) and true_count >= 8):
        return PlayerMove.SPLIT
    elif player_hand.total == 9 and dealer_card.value == 7 and true_count >= 7:
        return PlayerMove.STAY
    elif player_hand.total == 12 and dealer_card.value == 2 and true_count >= 7:
        return PlayerMove.STAY
    elif player_hand.total == 15 and dealer_card.value == 10 and true_count >= 6:
        return PlayerMove.STAY
    elif player_hand.total == 10 and dealer_card.value == 10 and true_count >= 5:
        return PlayerMove.DOUBLE
    elif player_hand.total == 12 and dealer_card.value == 3 and true_count >= 5:
        return PlayerMove.STAY
    elif player_hand.total == 10 and dealer_card.value == 11 and true_count >= 4:
        return PlayerMove.DOUBLE
    elif player_hand.total == 8 and dealer_card.value == 6 and true_count >= 3:
        return PlayerMove.DOUBLE
    elif player_hand.total == 19 and player_hand.has_usable_ace() and dealer_card.value == 6 and true_count >= 3:
        return PlayerMove.DOUBLE
    elif player_hand.total == 9 and dealer_card.value == 2 and true_count >= 1:
        return PlayerMove.DOUBLE
    elif player_hand.total == 14 and dealer_card.value == 2 and true_count >= 1:
        return PlayerMove.STAY
    elif player_hand.total == 13 and dealer_card.value == 2 and true_count <= -1:
        return PlayerMove.HIT
    elif player_hand.total == 16 and dealer_card.value == 10 and true_count <= -1:
        return PlayerMove.HIT
    elif player_hand.total == 12 and dealer_card.value == 5 and true_count <= -2:
        return PlayerMove.HIT
    elif player_hand.total == 13 and dealer_card.value == 3 and true_count <= -2:
        return PlayerMove.HIT
    elif player_hand.total == 12 and dealer_card.value == 6 and true_count <= -4:
        return PlayerMove.HIT
    elif player_hand.total == 11 and dealer_card.value == 11 and true_count <= -4:
        return PlayerMove.HIT
    return None


def get_player_move(player_hand: Hand, dealer_card: PlayingCard, true_count: float, can_split=False) -> PlayerMove:
    move = _get_true_count_play(player_hand, dealer_card, true_count)

    if move and move.value == PlayerMove.SPLIT.value and not can_split:
        move = None

    if move is None:
        if player_hand.has_pairs and can_split:
            return _get_pairs_play(player_hand, dealer_card)
        elif player_hand.has_ace and player_hand.total < 21 and player_hand.has_usable_ace():
            return _get_soft_play(player_hand, dealer_card)
        return _get_hard_play(player_hand, dealer_card)
    return move


def bd_nice_number(num: int, decimals: int = 1):
    suffixes = ['', 'k', 'M']
    order = 0 if num == 0 else min(len(suffixes) - 1, int(len(str(abs(int(num)))) - 1) // 3)
    scaled_num = num / (10 ** (3 * order))
    formatted_num = f"{scaled_num:.{decimals}f}{suffixes[order]}"
    return formatted_num


def print_table(results: dict, game_total: int):
    headers = ["Key", f"Wins/{bd_nice_number(game_total)}", "Win%"]
    table_data = []

    table: Union[PrettyTable, List] = []

    if USE_PRETTY_TABLE:
        table = PrettyTable()
        table.field_names = headers

    for key, value in results.items():
        data = [key, f"{value}", f"{(value / game_total * 100):.4f}"]
        table_data.append(data)

    if USE_PRETTY_TABLE:
        table.add_rows(table_data)
        with open('table.txt', 'w+') as logger:
            logger.write(str(table))
        # print(table)
    else:
        table_data = [headers] + table_data
        col_widths = [max(len(str(item)) for item in col) for col in zip(*table_data)]
        with open('table.txt', 'a+') as logger:
            for row in table_data:
                logger.write(" | ".join(f"{str(item):<{col_widths[i]}}" for i, item in enumerate(row)))
                logger.write("\n")
                if row == headers:
                    logger.write("-+-".join('-' * col_width for col_width in col_widths))
                    logger.write("\n")


__all__ = ["get_player_move", "print_table"]
