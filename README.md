# twrate 🇹🇼 — Taiwan Exchange Rate API and CLI for Python

`twrate` is a Python package and command-line tool for querying live foreign exchange rates from Taiwanese banks. It fetches TWD exchange-rate board data from multiple bank sources concurrently, so you can compare spot rates, cash rates, mid-rates, and spreads for currencies such as USD/TWD, JPY/TWD, EUR/TWD, and more.

Use `twrate` when you need a lightweight Taiwan exchange rate API for scripts, data pipelines, dashboards, or terminal-based rate checks.

## ✨ Features

- 🏦 **Taiwan bank exchange rates** from 17 supported banks.
- ⚡ **Async Python API** built for concurrent fan-out with `asyncio` and `httpx`.
- 💱 **CLI for quick lookup**: run `twrate USD` to compare USD/TWD rates across banks.
- 📊 **Normalized `Rate` model** with spot buy/sell, cash buy/sell, mid-rate, spread, currency pair, and fetch timestamp.
- ✅ **Typed package** with Pydantic validation and `py.typed` support.
- 🧩 **Bank-specific fetchers** that keep each source isolated and easy to maintain.

## 🏦 Supported Taiwanese banks

| Bank | Chinese name | Exchange enum |
| --- | --- | --- |
| Bank of Taiwan | 台灣銀行 | `Exchange.BOT` |
| DBS Bank Taiwan | 星展銀行 | `Exchange.DBS` |
| SinoPac Bank | 永豐銀行 | `Exchange.SINOPAC` |
| E.SUN Bank | 玉山銀行 | `Exchange.ESUN` |
| LINE Bank | LINE Bank | `Exchange.LINE` |
| HSBC Bank Taiwan | 匯豐銀行 | `Exchange.HSBC` |
| Next Bank | 將來銀行 | `Exchange.NEXT` |
| KGI Bank | 凱基銀行 | `Exchange.KGI` |
| Cathay United Bank | 國泰世華銀行 | `Exchange.CATHAY` |
| Mega International Commercial Bank | 兆豐銀行 | `Exchange.MEGABANK` |
| First Bank | 第一銀行 | `Exchange.FIRSTBANK` |
| Land Bank of Taiwan | 土地銀行 | `Exchange.LANDBANK` |
| Yuanta Bank | 元大銀行 | `Exchange.YUANTA` |
| Taishin Bank | 台新銀行 | `Exchange.TAISHIN` |
| Taichung Bank | 台中銀行 | `Exchange.TAICHUNG` |
| Taiwan Cooperative Bank | 合作金庫 | `Exchange.COOPERATIVE` |
| Fubon Bank | 台北富邦銀行 | `Exchange.FUBON` |

> Availability depends on each bank's public website or API. Some banks may publish only spot rates, only selected currencies, or temporarily unavailable data.

## 📦 Installation

`twrate` requires Python 3.12 or later.

```bash
pip install twrate
```

For local development, use `uv`:

```bash
uv sync
uv run twrate USD
```

You can also run the CLI without installing it into the current environment:

```bash
uvx twrate USD
```

## 🚀 Quick start

### 💱 Compare USD/TWD rates in the terminal

```bash
twrate USD
```

Example output:

```text
                            USD 各行即時牌價
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ 銀行                ┃ 即期買進 ┃ 即期賣出 ┃ 即期點差 ┃ 現鈔買進 ┃ 現鈔賣出 ┃ 現鈔點差 ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 台灣銀行 (Bank ... │ 30.0950  │ 30.2450  │ 0.50%    │ 29.7700  │ 30.4400  │ 2.22%    │
│ 星展銀行 (DBS ...  │ 30.0760  │ 30.2790  │ 0.67%    │ 29.8630  │ 30.4700  │ 2.01%    │
└─────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 🐍 Fetch rates from one bank in Python

```python
import asyncio

from twrate import Exchange, fetch_rates


async def main() -> None:
    rates = await fetch_rates(Exchange.BOT)

    usd_rates = [rate for rate in rates if rate.source == "USD"]
    for rate in usd_rates:
        print(rate.symbol, rate.spot_buy, rate.spot_sell, rate.spot_spread)


if __name__ == "__main__":
    asyncio.run(main())
```

### ⚡ Fetch all banks concurrently

```python
import asyncio

from twrate import Exchange, Rate, fetch_rates


async def fetch_all_rates() -> list[Rate]:
    tasks = [fetch_rates(exchange) for exchange in Exchange]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    rates: list[Rate] = []
    for exchange, result in zip(Exchange, results, strict=False):
        if isinstance(result, Exception):
            print(f"Failed to fetch {exchange.value}: {result}")
            continue

        rates.extend(result)

    return rates


if __name__ == "__main__":
    all_rates = asyncio.run(fetch_all_rates())
    usd_rates = [rate for rate in all_rates if rate.source == "USD"]
    print(usd_rates)
```

## 📊 `Rate` model

Each fetcher returns a list of normalized `Rate` objects:

| Field or property | Description |
| --- | --- |
| `exchange` | Bank identifier, such as `Exchange.BOT` or `Exchange.DBS`. |
| `source` | Source currency code, such as `USD`, `JPY`, or `EUR`. |
| `target` | Target currency code. For this package, it is usually `TWD`. |
| `spot_buy` | Bank spot buying rate. |
| `spot_sell` | Bank spot selling rate. |
| `cash_buy` | Bank cash buying rate, if available. |
| `cash_sell` | Bank cash selling rate, if available. |
| `fetched_at` | Timestamp generated when the `Rate` object is created. |
| `spot_mid` | Mid-rate calculated from `spot_buy` and `spot_sell`. |
| `cash_mid` | Mid-rate calculated from `cash_buy` and `cash_sell`. |
| `spot_spread` | Relative spread for spot transactions. |
| `cash_spread` | Relative spread for cash transactions. |
| `symbol` | Currency pair string, for example `USD/TWD`. |

Missing or zero bank values are normalized to `None`.

## 🛠️ Development

Install dependencies and run commands through `uv`:

```bash
uv sync
uv run pytest
uv run twrate USD
```

Run the full test suite with coverage:

```bash
uv run pytest -v -s --cov=src tests
```

## 🤝 Contributing

Contributions are welcome. Good first issues include:

- Fixing a bank fetcher when a public page or API changes.
- Adding tests and sample fixtures for existing fetchers.
- Improving parsing for currencies with partial spot or cash data.
- Adding a new Taiwanese bank source while preserving the shared `Rate` model.

When adding or updating a fetcher, keep it bank-specific, async-first, and covered by tests where possible.

## 📄 License

`twrate` is released under the terms in [LICENSE](LICENSE).
