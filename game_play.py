from bj import Blackjack
from config import EXPORT_FILE


if __name__ == '__main__':
    try:
        open(EXPORT_FILE, 'w').close()
        for _ in range(1):
            bj = Blackjack()
            bj.run()
            print(" ")
    except KeyboardInterrupt:
        print("Exiting...")
        input(">>> ")
        exit()
