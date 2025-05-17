from rich import print

from twrate.bot import query_bot_rates
from twrate.dbs import query_dbs_rates


def main() -> None:
    print(query_bot_rates())
    print(query_dbs_rates())


if __name__ == "__main__":
    main()
