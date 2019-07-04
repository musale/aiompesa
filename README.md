# aiompesa

A package for accessing the [MPESA Daraja API](https://developers.safaricom.co.ke>) from [asyncio](https://docs.python.org/3/library/asyncio.html>).

## Usage

```python
import asyncio
from aiompesa import Mpesa

CONSUMER_KEY = "nF4OwB2XiuYZwmdMz3bovnzw2qMls1b7"
CONSUMER_SECRET = "biIImmaAX9dYD4Pw"

loop = asyncio.get_event_loop()
mpesa = Mpesa(True, CONSUMER_KEY, CONSUMER_SECRET)

token_response = loop.run_until_complete(mpesa.generate_token())

access_token = token_response.get("access_token", None)
expires_in = token_response.get("expires_in", None)
if access_token is None:
    print("Error: Wrong credentials used to get the access_token")
else:
    print(f"access_token = {access_token}, expires_in = {expires_in} secs")
```

## Requirements

- Python 3.6+

## Installation

`$ pip install aiompesa`

## Motivation

- To learn a little more about `asyncio` and put it to some practise.
- To develop an async wrapper for the [Safaricom daraja api](https://developers.safaricom.co.ke).

## Contribution

Follow the [contribution guidelines](https://github.com/musale/aiompesa)
