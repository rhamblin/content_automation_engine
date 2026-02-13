# Amazon Affiliate

Fetches product info and generates affiliate links via the Amazon Creators API SDK. Supports product search, ASIN lookup, and Amazon URL parsing. Always returns product image URLs when available.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Add your Creators API credentials to `amazon-credentials.json`
3. The bundled `creatorsapi-python-sdk/` is used automatically (no separate install needed)

## Usage

```bash
# Get product info by ASIN
python amazon_affiliate.py get B0BSHF7WHW

# Get product info from Amazon URL
python amazon_affiliate.py url "https://www.amazon.com/dp/B0BSHF7WHW"

# Search for products
python amazon_affiliate.py search "wireless earbuds"

# Generate affiliate link (no API call)
python amazon_affiliate.py link B0BSHF7WHW

# Output as JSON
python amazon_affiliate.py get B0BSHF7WHW --json
```
