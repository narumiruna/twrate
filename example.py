from rich import print

from twrate import Exchange
from twrate import fetch_rates


def main() -> None:
    for exchange in Exchange:
        print(fetch_rates(exchange))


if __name__ == "__main__":
    main()
