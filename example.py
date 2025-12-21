import asyncio

from rich import print

from twrate import Exchange
from twrate import fetch_rates


async def main() -> None:
    for exchange in Exchange:
        rates = await fetch_rates(exchange)
        print(rates)


if __name__ == "__main__":
    asyncio.run(main())
