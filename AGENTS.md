# Agents Architecture

## Overview

`twrate` implements a fetcher-based architecture where each agent (fetcher) is responsible for retrieving exchange rate data from a specific Taiwanese bank. The system uses a consistent data model (`Rate`) across all fetchers, enabling seamless integration and comparison of rates from different sources.

## Core Components

### Rate Model (`types.py`)

The `Rate` class is the central data structure that standardizes exchange rate information across all fetchers:

```python
class Rate(BaseModel):
    exchange: Exchange          # Bank identifier
    source: str                # Source currency code
    target: str                # Target currency (typically "TWD")
    spot_buy: float | None     # Bank's buying rate for spot transactions
    spot_sell: float | None    # Bank's selling rate for spot transactions
    cash_buy: float | None     # Bank's buying rate for cash transactions
    cash_sell: float | None    # Bank's selling rate for cash transactions
    fetched_at: datetime       # Timestamp of fetch operation
```

**Computed Properties:**
- `spot_mid`: Average of spot buy/sell rates
- `cash_mid`: Average of cash buy/sell rates
- `spot_spread`: Relative spread for spot transactions
- `cash_spread`: Relative spread for cash transactions
- `symbol`: Formatted currency pair string

### Exchange Enum (`types.py`)

Defines supported banks:
- `DBS`: DBS Bank Taiwan (星展銀行)
- `SINOPAC`: Sinopac Bank (永豐銀行)
- `BOT`: Bank of Taiwan (台灣銀行)
- `ESUN`: E.SUN Bank (玉山銀行)
- `LINE`: Line Bank (LINE Bank)

## Fetcher Agents

Each fetcher agent implements a `fetch_*_rates()` function that returns a `list[Rate]`. The architecture follows these principles:

1. **Single Responsibility**: Each fetcher handles one bank only
2. **Consistent Interface**: All fetchers return `list[Rate]`
3. **Error Handling**: HTTP errors propagate via `httpx.raise_for_status()`
4. **Data Validation**: Use Pydantic models for response parsing

### 1. Bank of Taiwan Fetcher (`bot.py`)

**Data Source**: Text-based API
**URL**: `https://rate.bot.com.tw/xrt/fltxt/0/day`
**Format**: Plain text with space-separated columns

**Implementation Details:**
- Parses text response with UTF-8-SIG encoding
- Validates header structure before processing
- Extracts rates from fixed column positions
- Supports spot and cash rates for all currencies

**Key Features:**
- Header validation ensures data structure integrity
- Handles Chinese column headers
- Simple parsing strategy suitable for stable text format

### 2. DBS Bank Fetcher (`dbs.py`)

**Data Source**: REST API
**URL**: `https://www.dbs.com.tw/tw-rates-api/v1/api/twrates/latestForexRates`
**Format**: JSON

**Implementation Details:**
- Uses Pydantic models for JSON deserialization
- Nested structure: `DBSRateResponse` → `Results` → `Asset` → `RecDatum`
- Includes timestamp information (last updated, effective date)
- Handles missing cash rates (set to `None`)

**Key Features:**
- Type-safe parsing with Pydantic
- Validation aliasing for API field mapping
- Custom validators for string-to-float conversion

### 3. E.SUN Bank Fetcher (`esun.py`)

**Data Source**: REST API
**URL**: `https://www.esunbank.com/api/client/ExchangeRate/LastRateInfo`
**Format**: JSON (POST request)

**Implementation Details:**
- POST request to API endpoint
- Complex timestamp parsing (Unix timestamp in string format)
- Handles missing cash rates with dash ("-") placeholder
- Parses currency pair from single field

**Key Features:**
- Custom datetime validator for `/Date(timestamp)/` format
- Splits `CCY` field to extract source/target currencies
- Handles promotional rate information (bonus fields)

### 4. Line Bank Fetcher (`line.py`)

**Data Source**: HTML scraping
**URL**: `https://www.linebank.com.tw/board-rate/exchange-rate`
**Format**: HTML

**Implementation Details:**
- Uses BeautifulSoup for HTML parsing
- Selects specific table cells with CSS selectors
- Returns single currency pair (USD/TWD only)
- Spot rates only (no cash rates)

**Key Features:**
- Simplest fetcher (single currency)
- HTML scraping approach
- Text extraction with normalization

### 5. Sinopac Bank Fetcher (`sinopac.py`)

**Data Source**: REST API
**URL**: Multiple endpoints for remit and cash rates
**Format**: JSON

**Implementation Details:**
- Fetches both remit (spot) and cash rates separately
- Merges two datasets using `merge_rates()` function
- Complex nested Pydantic models
- Handles missing rates with dash ("-") placeholder

**Key Features:**
- Dual-endpoint architecture
- Rate merging logic to combine spot and cash
- Comprehensive data structure validation

## Fetcher Selection (`fetcher.py`)

The `fetch_rates()` function acts as a dispatcher:

```python
def fetch_rates(exchange: Exchange) -> list[Rate]:
    match exchange:
        case Exchange.SINOPAC:
            return fetch_sinopac_rates()
        case Exchange.ESUN:
            return fetch_esun_rates()
        case Exchange.LINE:
            return fetch_line_rates()
        case Exchange.BOT:
            return fetch_bot_rates()
        case Exchange.DBS:
            return fetch_dbs_rates()
```

## Adding New Fetchers

To add support for a new bank:

1. **Create fetcher module** in `src/twrate/fetchers/`
2. **Add Exchange enum value** in `types.py`
3. **Implement `fetch_*_rates()`** following the pattern:
   - Accept no parameters
   - Return `list[Rate]`
   - Handle HTTP requests with `httpx`
   - Parse response to `Rate` objects
   - Use Pydantic for complex JSON structures
4. **Update dispatcher** in `fetcher.py`
5. **Add test cases** in `tests/`

### Fetcher Template

```python
import httpx
from ..types import Exchange, Rate

def fetch_example_rates() -> list[Rate]:
    url = "https://example.bank.com/api/rates"
    resp = httpx.get(url)
    resp.raise_for_status()

    # Parse response and convert to Rate objects
    rates = []
    for item in resp.json():
        rate = Rate(
            exchange=Exchange.EXAMPLE,
            source=item["currency"],
            target="TWD",
            spot_buy=item["buy"],
            spot_sell=item["sell"],
            cash_buy=item.get("cash_buy"),
            cash_sell=item.get("cash_sell"),
        )
        rates.append(rate)

    return rates
```

## Data Flow

```
User Request → CLI/API Entry Point
       ↓
fetch_rates(exchange)
       ↓
Specific Fetcher (e.g., fetch_dbs_rates)
       ↓
HTTP Request → Bank API/Website
       ↓
Response Parsing (Text/JSON/HTML)
       ↓
Rate Object Creation
       ↓
Return list[Rate]
```

## Design Patterns

### 1. Strategy Pattern
Each fetcher implements the same interface but with different strategies for data retrieval and parsing.

### 2. Factory Pattern
The `fetch_rates()` function acts as a factory, creating the appropriate fetcher based on the `Exchange` enum.

### 3. Builder Pattern
Pydantic models build complex objects from raw API responses with validation.

### 4. Single Source of Truth
All fetchers converge to the same `Rate` model, ensuring consistency.

## Error Handling

Fetchers follow these error handling principles:

1. **HTTP Errors**: Propagate via `httpx.raise_for_status()`
2. **Parsing Errors**: Let Pydantic validation errors bubble up
3. **Data Validation**: Use field validators to handle edge cases
4. **Missing Data**: Return `None` for optional fields rather than failing

## Testing

Each fetcher has corresponding test cases in `tests/test_fetcher.py`:
- Uses pytest framework
- Test data stored in `tests/data/`
- Tests verify Rate object structure and values
- Integration tests make real API calls (when appropriate)

## Performance Considerations

- **HTTP Client**: Uses `httpx` for async-ready implementation
- **Parsing**: Pydantic provides efficient parsing with C extensions
- **Caching**: Not implemented at fetcher level (can be added at application layer)
- **Rate Limiting**: Fetchers don't implement throttling (application responsibility)

## Dependencies

- **httpx**: HTTP client for API requests
- **pydantic**: Data validation and parsing
- **beautifulsoup4**: HTML parsing (Line Bank only)
- **loguru**: Logging framework

## Future Enhancements

Potential improvements for the agent architecture:

1. **Async Support**: Convert fetchers to async/await pattern
2. **Retry Logic**: Add exponential backoff for failed requests
3. **Caching Layer**: Implement response caching with TTL
4. **Rate Limiting**: Add per-bank rate limit enforcement
5. **Health Checks**: Monitor API availability
6. **Historical Data**: Support time-series rate retrieval
7. **Webhook Support**: Real-time rate updates
8. **Multi-Currency**: Support non-TWD target currencies
