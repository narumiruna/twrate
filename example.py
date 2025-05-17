from rich import print

from twrate import query_bot_rates
from twrate import query_dbs_rates
from twrate import query_esun_rates
from twrate import query_sinopac_rates


def main() -> None:
    print(query_esun_rates())
    print(query_sinopac_rates())
    print(query_bot_rates())
    print(query_dbs_rates())


if __name__ == "__main__":
    main()
