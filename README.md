# twrate

A Python package for querying real-time exchange rates from major Taiwanese banks.

## Overview

`twrate` provides a simple and efficient way to retrieve up-to-date currency exchange rates from Taiwanese banks. Currently, it supports the following banks:

- Bank of Taiwan (台灣銀行)
- DBS Bank Taiwan (星展銀行)
- Sinopac Bank (永豐銀行)
- E.SUN Bank (玉山銀行)
- Line Bank (LINE Bank)

## Installation

```bash
pip install twrate
```

## Usage

### Basic Usage

```python
from rich import print

from twrate import Exchange
from twrate import fetch_rates

for exchange in Exchange:
    print(fetch_rates(exchange))
```

### Command-Line Interface

You can also use `twrate` directly from the command line:

```bash
# Query exchange rates for USD from all supported banks
twrate USD
```

Example output:
```
Exchange          Spot Buy    Spot Sell    Cash Buy    Cash Sell
--------------  ----------  -----------  ----------  -----------
BANK_OF_TAIWAN      30.095       30.245      29.77        30.44
DBS                 30.076       30.279      29.863       30.47
SINOPAC             30.092       30.203      29.892       30.403
ESUN                30.1         30.2        29.85        30.4
```

### Rate Information

The `Rate` object provides the following information:

- `exchange`: The bank code (e.g., "BOT" for Bank of Taiwan, "DBS" for DBS Bank)
- `source`: The source currency code
- `target`: The target currency code (always "TWD")
- `spot_buy`: The bank's buying rate for spot transactions
- `spot_sell`: The bank's selling rate for spot transactions
- `cash_buy`: The bank's buying rate for cash transactions
- `cash_sell`: The bank's selling rate for cash transactions
- `spot_mid`: A calculated property that returns the mid-rate between spot buy and sell

## License

See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Currently, the package supports Bank of Taiwan and DBS Bank, but you can help extend the functionality to cover more Taiwanese banks.
