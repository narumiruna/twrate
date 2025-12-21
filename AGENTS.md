# Agents Architecture

## Overview

`twrate` implements a fetcher-based architecture where each agent (fetcher) is responsible for retrieving exchange rate data from a specific Taiwanese bank. Fetchers are asynchronous coroutines and run in parallel, giving fast fan-out across sources. The system uses a consistent data model (`Rate`) across all fetchers, enabling seamless integration and comparison of rates from different sources.

## Development Workflow

### Running the Application

Use `uv` for all Python-related operations:

```bash
# Run the CLI to fetch rates for a specific currency
uv run twrate USD

# Run tests
uv run pytest

# Install dependencies
uv sync

# Add a new dependency
uv add <package-name>

# Run Python scripts or one-liners (ALWAYS use this instead of python3)
uv run python script.py
uv run python -c "import httpx; print(httpx.__version__)"
```

**Why `uv`?**
- Fast dependency resolution and installation
- Automatic virtual environment management
- Consistent across development, testing, and CI/CD
- Lock file (`uv.lock`) ensures reproducible builds

**Important:** Always use `uv run python` instead of `python3` or `python` when running scripts or testing code. This ensures you're using the correct environment with all dependencies properly loaded.

## Core Components

### Rate Model (`types.py`)

The `Rate` class is the central data structure that standardizes exchange rate information across all fetchers:

```python
class Rate(BaseModel):
    exchange: Exchange          # Bank identifier
    source: str                 # Source currency code
    target: str                 # Target currency (typically "TWD")
    spot_buy: float | None      # Bank's buying rate for spot transactions
    spot_sell: float | None     # Bank's selling rate for spot transactions
    cash_buy: float | None      # Bank's buying rate for cash transactions
    cash_sell: float | None     # Bank's selling rate for cash transactions
    fetched_at: datetime        # Timestamp of fetch operation
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
- `HSBC`: HSBC Bank Taiwan (匯豐銀行)
- `NEXT`: Next Bank (將來銀行)
- `KGI`: KGI Bank (凱基銀行)
- `CATHAY`: Cathay United Bank (國泰世華銀行)

## Fetcher Agents

Each fetcher agent implements an `async def fetch_*_rates()` coroutine that resolves to a `list[Rate]`. The architecture follows these principles:

1. **Single Responsibility**: Each fetcher handles one bank only
2. **Consistent Interface**: All fetchers return `list[Rate]`
3. **Error Handling**: HTTP errors propagate via `httpx.raise_for_status()`
4. **Data Validation**: Use Pydantic models for response parsing
5. **Async First**: Use `httpx.AsyncClient` and `asyncio.gather()` for concurrent fan-out

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

### 6. HSBC Bank Fetcher (`hsbc.py`)

**Data Source**: HTML scraping
**URL**: `https://www.hsbc.com.tw/currency-rates/`
**Format**: HTML

**Implementation Details:**
- Uses BeautifulSoup for HTML parsing
- Extracts currency codes from table cells using regex
- Parses structured table with tbody element
- Handles missing rates with dash ("-") placeholder

**Key Features:**
- HTML table scraping approach
- Regex-based currency code extraction
- Simple parse_rate helper function
- Follows redirects for proper page loading

### 7. Next Bank Fetcher (`nextbank.py`)

**Data Source**: HTML scraping
**URL**: `https://www.nextbank.com.tw/exchange-rates`
**Format**: HTML

**Implementation Details:**
- Uses BeautifulSoup for HTML parsing
- Extracts currency codes from table cells using regex patterns
- Validates 3-letter ISO currency codes
- Skips rows without valid currency codes
- Handles missing rates gracefully

**Key Features:**
- HTML table scraping approach
- Dual pattern matching for currency codes (with/without parentheses)
- Defensive column access with length checks
- Descriptive error messages for debugging

### 8. KGI Bank Fetcher (`kgi.py`)

**Data Source**: HTML scraping
**URL**: `https://www.kgibank.com.tw/zh-tw/personal/interest-rate/fx`
**Format**: HTML

**Implementation Details:**
- Scrapes desktop and mobile table layouts using CSS selectors
- Parses four numeric columns per currency: spot buy/sell and cash buy/sell
- Accepts dashes as missing values; validates currency code presence

**Key Features:**
- Async HTTP requests with `httpx.AsyncClient`
- Regex guards to keep only numeric or dash cells
- Raises when no rates are parsed to surface page shape changes

### 9. Cathay United Bank Fetcher (`cathay.py`)

**Data Source**: HTML scraping
**URL**: `https://www.cathaybk.com.tw/cathaybk/personal/product/deposit/currency-billboard/`
**Format**: HTML

**Implementation Details:**
- Uses BeautifulSoup for HTML parsing
- Extracts currency sections from `div.cubre-o-table__item.currency` containers
- Parses currency code from `div.cubre-m-currency__name` (format: "美元USD")
- Extracts spot and cash rates from table rows
- Handles missing rates with dash ("--") placeholder

**Key Features:**
- Clean HTML structure with well-defined CSS classes
- Supports 16+ currencies
- Simple table parsing with clear row identification ("即期匯率", "現鈔匯率")
- Data available in initial HTML (no JavaScript rendering required)

## Fetcher Selection (`fetcher.py`)

The `fetch_rates()` function acts as a dispatcher:

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

## Adding New Fetchers

To add support for a new bank:

1. **Create fetcher module** in `src/twrate/fetchers/`
2. **Add Exchange enum value** in `types.py`
3. **Implement `async def fetch_*_rates()`** following the pattern:
    - Accept no parameters
    - Return `list[Rate]`
    - Handle HTTP requests with `httpx.AsyncClient`
    - Parse response to `Rate` objects
    - Use Pydantic for complex JSON structures
4. **Update dispatcher** in `fetcher.py`
5. **Add test cases** in `tests/`

### Fetcher Template

```python
import httpx
from ..types import Exchange, Rate

async def fetch_example_rates() -> list[Rate]:
    url = "https://example.bank.com/api/rates"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
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

## Troubleshooting and Lessons Learned

### Issue: JavaScript-Rendered Content (Taishin Bank Case Study)

**Problem Description:**
When implementing the Taishin Bank fetcher, we encountered a critical issue where the standard `httpx` + `BeautifulSoup` approach failed to extract any data.

**Investigation Process:**

1. **Initial Symptoms**
   ```python
   tables = soup.find_all('table')
   print(f'Tables found: {len(tables)}')  # Result: 0
   ```
   - Initial HTTP GET returned HTML with no table elements
   - Content appeared to be present when viewing in browser

2. **Diagnostic Steps**
   - Used Playwright MCP to inspect the fully-rendered page
     - Confirmed tables exist after JavaScript execution
     - Found nested table structure with currency data
   - Checked network requests for separate API endpoints
     - No dedicated API found for rate data
   - Examined page source for embedded JSON data in `<script>` tags
     - Data not embedded in page source

3. **Root Cause Analysis**
   ```
   Browser Request → Initial HTML (no tables)
                  ↓
           JavaScript Execution
                  ↓
         DOM Manipulation (tables created)
                  ↓
           Fully Rendered Page
   ```

   **Key Finding**: Taishin Bank's exchange rate table is generated entirely via client-side JavaScript, making it invisible to traditional HTTP scraping.

**Technical Verification:**
```bash
# Test with httpx (fails)
uv run python -c "
import httpx
from bs4 import BeautifulSoup
resp = httpx.get('https://www.taishinbank.com.tw/TSB/personal/deposit/lookup/realtime/')
soup = BeautifulSoup(resp.text, 'html.parser')
print(f'Tables: {len(soup.find_all(\"table\"))}')  # 0
print('USD in response:', '美元USD' in resp.text)  # False
"

# Test with Playwright (succeeds)
# - Can extract table data after page load
# - Tables visible in DOM after JavaScript execution
```

**Solution Options Evaluated:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Selenium/Playwright** | ✅ Full browser automation<br>✅ Handles all JS rendering<br>✅ Most reliable | ❌ Heavy dependencies (100+ MB)<br>❌ Slower execution<br>❌ Browser installation required | ❌ Rejected for now |
| **Reverse Engineer JS** | ✅ Lightweight solution<br>✅ Fast execution | ❌ Time-consuming analysis<br>❌ Brittle (breaks if JS changes)<br>❌ May encounter obfuscation | ❌ Not pursued |
| **Accept Limitation** | ✅ Maintains lightweight design<br>✅ No new dependencies<br>✅ Fast for other banks | ❌ Missing one data source | ✅ **Adopted** |

**Current Status:**
- Fetcher code exists but returns empty results
- Error is logged but doesn't crash the application
- Other supported banks continue to function normally

**Lessons for Future Implementations:**

1. **Early Detection**: Test with actual HTTP requests during initial investigation, not just browser inspection
2. **Network Analysis**: Always check browser DevTools Network tab for API calls before scraping HTML
3. **Progressive Enhancement**: Start with simplest approach (REST API > Static HTML > Dynamic HTML)
4. **Graceful Degradation**: Design fetchers to fail independently without affecting others
5. **Documentation**: Document technical limitations clearly for future maintainers

**Decision Framework for Similar Issues:**

```python
def evaluate_data_source(url: str) -> str:
    """
    Decision tree for choosing scraping approach.
    """
    # 1. Check for API
    if has_public_api(url):
        return "Use REST API fetcher"

    # 2. Check for static HTML
    if data_in_initial_html(url):
        return "Use httpx + BeautifulSoup"

    # 3. Check for embedded JSON
    if data_in_script_tags(url):
        return "Parse JSON from script tags"

    # 4. JavaScript-rendered content
    if requires_js_execution(url):
        if is_critical_data_source():
            return "Use Playwright/Selenium"
        else:
            return "Skip or mark as unsupported"

    return "Investigate further"
```

**Impact on Architecture:**
- Reinforced the importance of parallel fetching (one failure doesn't block others)
- Validated the error handling strategy (log errors, continue execution)
- Highlighted the trade-off between coverage and simplicity

### Best Practices Summary

1. **Verify Early**: Test data extraction with actual code before committing to an approach
2. **Use the Right Tool**: Match the tool to the data source complexity
3. **Fail Gracefully**: Design for partial success in multi-source systems
4. **Document Thoroughly**: Record technical limitations and decision rationale
5. **Maintain Focus**: Don't over-engineer solutions for edge cases

## Future Enhancements

Potential improvements for the agent architecture:

1. **Retry Logic**: Add exponential backoff for failed requests
2. **Caching Layer**: Implement response caching with TTL
3. **Rate Limiting**: Add per-bank rate limit enforcement
4. **Health Checks**: Monitor API availability
5. **Historical Data**: Support time-series rate retrieval
6. **Webhook Support**: Real-time rate updates
7. **Multi-Currency**: Support non-TWD target currencies
8. **Optional Browser Automation**: Add Playwright as optional dependency for JS-heavy sites
9. **Timeouts & Cancellation**: Add client timeouts, cancellation, and structured error propagation
