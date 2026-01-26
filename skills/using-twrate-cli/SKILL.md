---
name: using-twrate-cli
description: Use when fetching or comparing Taiwan bank FX rates via the twrate CLI, or when CLI output is empty or shows fetch errors.
---

# Using twrate CLI

## Overview
Use `uvx twrate <SOURCE>` to fetch live rates from supported banks and view a sorted comparison table (spot spread).

## When to Use
- Need USD/JPY/EUR rates to TWD across banks
- Need the best/lowest spot spread quickly
- CLI shows errors for individual banks but other banks still return data

## Quick Reference
- `uvx twrate USD` - fetch USD/TWD rates
- `uvx twrate JPY`
- `uvx twrate EUR`
- Output columns: Exchange, Spot Buy/Sell/Spread, Cash Buy/Sell/Spread
- Sorting: ascending by Spot Spread; missing spreads sink to the bottom

## Implementation
```bash
uvx twrate USD
```
Notes:
- `source_currency` is case-insensitive; unknown codes yield an empty table.
- Each bank fetch runs in parallel; failures log an error but do not stop others.

## Common Mistakes
- Running `python` directly instead of `uvx` (wrong environment)
- Using `TWD` as source (table usually empty; target is TWD)
- Treating logged fetch errors as total failure (check the table for available banks)

## Troubleshooting
- SSL certificate errors for a bank: retry later and check system certificates; other banks can still be used.
- Empty table: verify a 3-letter currency code (USD, JPY, EUR).
