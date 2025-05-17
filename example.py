from rich import print

from twrate import fetch_bot_rates
from twrate import fetch_dbs_rates
from twrate import fetch_esun_rates
from twrate import fetch_line_rates
from twrate import fetch_sinopac_rates


def main() -> None:
    print(fetch_line_rates())
    print(fetch_esun_rates())
    print(fetch_sinopac_rates())
    print(fetch_bot_rates())
    print(fetch_dbs_rates())


if __name__ == "__main__":
    main()
