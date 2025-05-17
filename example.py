from rich import print

from twrate.sinopac import query_sinopac_rates


def main() -> None:
    print(query_sinopac_rates())
    # print(query_bot_rates())
    # print(query_dbs_rates())


if __name__ == "__main__":
    main()
