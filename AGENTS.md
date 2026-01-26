# Agents Architecture

## Purpose

`twrate` uses a fetcher-based architecture: each async fetcher pulls exchange rates from one Taiwanese bank and returns a shared `Rate` model. Fetchers run concurrently for fast fan-out and easy comparison across sources.

## Workflow

Use `uv` for all Python operations:

```bash
# Fetch rates
uv run twrate USD

# Tests
uv run pytest

# Dependencies
uv sync
uv add <package-name>

# Run scripts / one-liners (always use uv)
uv run python script.py
uv run python -c "import httpx; print(httpx.__version__)"
```

Why `uv`:
- Fast dependency management
- Managed virtualenv
- Reproducible via `uv.lock`

Important: Always use `uv run python` instead of `python` or `python3`.

## Core Models

### Rate (`types.py`)

```python
class Rate(BaseModel):
    exchange: Exchange          # Bank identifier
    source: str                 # Source currency code
    target: str                 # Target currency (usually "TWD")
    spot_buy: float | None
    spot_sell: float | None
    cash_buy: float | None
    cash_sell: float | None
    fetched_at: datetime
```

Computed properties:
- `spot_mid`, `cash_mid`
- `spot_spread`, `cash_spread`
- `symbol`

### Exchange (`types.py`)

Supported banks:
- `DBS`, `SINOPAC`, `BOT`, `ESUN`, `LINE`, `HSBC`, `NEXT`, `KGI`, `CATHAY`

## Fetcher Contract

Each fetcher exposes `async def fetch_*_rates() -> list[Rate]` and follows:
1. Single bank responsibility
2. Consistent return type (`list[Rate]`)
3. HTTP errors via `raise_for_status()`
4. Pydantic for validation
5. Async first (`httpx.AsyncClient`, `asyncio.gather()`)

## Fetchers by Bank

- **BOT** (`bot.py`) — Text API `https://rate.bot.com.tw/xrt/fltxt/0/day`; UTF-8-SIG parsing; fixed columns; spot + cash.
- **DBS** (`dbs.py`) — JSON API `https://www.dbs.com.tw/tw-rates-api/v1/api/twrates/latestForexRates`; nested Pydantic models; cash often missing.
- **ESUN** (`esun.py`) — JSON POST `https://www.esunbank.com/api/client/ExchangeRate/LastRateInfo`; `/Date(ts)/` parsing; dash as missing.
- **LINE** (`line.py`) — HTML `https://www.linebank.com.tw/board-rate/exchange-rate`; USD/TWD only; spot only.
- **SINOPAC** (`sinopac.py`) — Two JSON endpoints; merge spot + cash via `merge_rates()`.
- **HSBC** (`hsbc.py`) — HTML `https://www.hsbc.com.tw/currency-rates/`; regex currency codes; dash as missing.
- **NEXT** (`nextbank.py`) — HTML `https://www.nextbank.com.tw/exchange-rates`; strict ISO currency validation.
- **KGI** (`kgi.py`) — HTML `https://www.kgibank.com.tw/zh-tw/personal/interest-rate/fx`; desktop/mobile tables; numeric-or-dash guard.
- **CATHAY** (`cathay.py`) — HTML `https://www.cathaybk.com.tw/cathaybk/personal/product/deposit/currency-billboard/`; clean CSS structure; spot + cash.

## Dispatcher

`fetch_rates()` in `fetcher.py` routes to the correct fetcher by `Exchange`.

```python
async def fetch_rates(exchange: Exchange) -> list[Rate]:
    match exchange:
        case Exchange.SINOPAC:
            return await fetch_sinopac_rates()
        case Exchange.ESUN:
            return await fetch_esun_rates()
        case Exchange.LINE:
            return await fetch_line_rates()
        case Exchange.BOT:
            return await fetch_bot_rates()
        case Exchange.DBS:
            return await fetch_dbs_rates()
        case Exchange.HSBC:
            return await fetch_hsbc_rates()
        case Exchange.NEXT:
            return await fetch_nextbank_rates()
        case Exchange.KGI:
            return await fetch_kgi_rates()
        case Exchange.CATHAY:
            return await fetch_cathay_rates()
        case _:
            raise ValueError(f"Unsupported exchange: {exchange}")
```

## Adding a Fetcher

1. Create a module in `src/twrate/fetchers/`.
2. Add an `Exchange` enum value in `types.py`.
3. Implement `async def fetch_*_rates()` returning `list[Rate]`.
4. Wire it in `fetcher.py`.
5. Add tests in `tests/`.

Template:

```python
import httpx
from ..types import Exchange, Rate

async def fetch_example_rates() -> list[Rate]:
    url = "https://example.bank.com/api/rates"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()

        rates = []
        for item in resp.json():
            rates.append(
                Rate(
                    exchange=Exchange.EXAMPLE,
                    source=item["currency"],
                    target="TWD",
                    spot_buy=item["buy"],
                    spot_sell=item["sell"],
                    cash_buy=item.get("cash_buy"),
                    cash_sell=item.get("cash_sell"),
                )
            )

    return rates
```

## Error Handling

- HTTP errors bubble up (`raise_for_status()`).
- Pydantic validation errors bubble up.
- Missing values use `None` (or parsed dash placeholders).

## Testing

- Unit tests: `tests/test_fetcher.py`
- Sample data: `tests/data/`
- Integration tests may hit real endpoints.

## Dependencies

- `httpx`
- `pydantic`
- `beautifulsoup4`
- `loguru`

## Troubleshooting: JS-rendered Pages (Taishin Case)

Summary: Taishin’s rate table is client-side rendered, so `httpx + BeautifulSoup` returns no data. Playwright can render it but adds heavy deps.

Verification:
```bash
uv run python -c "\
import httpx; from bs4 import BeautifulSoup; \
resp = httpx.get('https://www.taishinbank.com.tw/TSB/personal/deposit/lookup/realtime/'); \
soup = BeautifulSoup(resp.text, 'html.parser'); \
print(f'Tables: {len(soup.find_all(\"table\"))}'); \
print('USD in response:', '美元USD' in resp.text)\
"
```

Decision: keep fetcher lightweight and accept no data for JS-only sites unless the source is critical.

## Future Enhancements

- Retry with backoff
- Caching with TTL
- Rate limiting per bank
- Health checks
- Historical rates
- Optional Playwright for JS-heavy sites
