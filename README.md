# twrate

A Python package for querying real-time exchange rates from major Taiwanese banks.

## Overview

`twrate` provides a simple and efficient way to retrieve up-to-date currency exchange rates from Taiwanese banks. Currently, it supports the following banks:

- Bank of Taiwan (台灣銀行)
- DBS Bank Taiwan (星展銀行)
- Sinopac Bank (永豐銀行)

## Installation

```bash
pip install twrate
```

## Usage

### Basic Usage

```python
from twrate.bot import query_bot_rates  # Bank of Taiwan
from twrate.dbs import query_dbs_rates  # DBS Bank

# Get exchange rates from Bank of Taiwan
bot_rates = query_bot_rates()
print(bot_rates)

# Get exchange rates from DBS Bank
dbs_rates = query_dbs_rates()
print(dbs_rates)
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
