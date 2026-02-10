"""Amazon Affiliate Tool - fetch affiliate links and product info via PA-API 5.0."""

import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

# PA-API 5.0 endpoints by region
REGIONS = {
    "us": {"host": "webservices.amazon.com", "region": "us-east-1"},
    "uk": {"host": "webservices.amazon.co.uk", "region": "eu-west-1"},
    "de": {"host": "webservices.amazon.de", "region": "eu-west-1"},
    "fr": {"host": "webservices.amazon.fr", "region": "eu-west-1"},
    "jp": {"host": "webservices.amazon.co.jp", "region": "us-west-2"},
    "ca": {"host": "webservices.amazon.ca", "region": "us-east-1"},
    "au": {"host": "webservices.amazon.com.au", "region": "us-west-2"},
}


def load_credentials() -> dict:
    """Load Amazon PA-API credentials from file."""
    creds_path = Path(__file__).parent / "amazon-credentials.json"
    if not creds_path.exists():
        print(f"Error: Credentials file not found at {creds_path}")
        print("Create amazon-credentials.json with:")
        print(json.dumps({
            "access_key": "YOUR_ACCESS_KEY",
            "secret_key": "YOUR_SECRET_KEY",
            "partner_tag": "YOUR_ASSOCIATE_TAG-20",
            "region": "us"
        }, indent=2))
        sys.exit(1)
    return json.loads(creds_path.read_text())


class AmazonAffiliate:
    """Amazon Product Advertising API 5.0 client."""

    def __init__(self, access_key: str, secret_key: str, partner_tag: str, region: str = "us"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.region_config = REGIONS.get(region, REGIONS["us"])
        self.host = self.region_config["host"]
        self.aws_region = self.region_config["region"]
        self.service = "ProductAdvertisingAPI"

    def _sign(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _get_signature_key(self, date_stamp: str) -> bytes:
        k_date = self._sign(f"AWS4{self.secret_key}".encode("utf-8"), date_stamp)
        k_region = self._sign(k_date, self.aws_region)
        k_service = self._sign(k_region, self.service)
        return self._sign(k_service, "aws4_request")

    def _make_request(self, operation: str, payload: dict) -> dict:
        """Make signed request to PA-API."""
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        # Request details
        method = "POST"
        uri = f"/paapi5/{operation.lower()}"
        headers_to_sign = {
            "content-encoding": "amz-1.0",
            "content-type": "application/json; charset=utf-8",
            "host": self.host,
            "x-amz-date": amz_date,
            "x-amz-target": f"com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{operation}",
        }

        body = json.dumps(payload)
        payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        # Canonical request
        signed_headers = ";".join(sorted(headers_to_sign.keys()))
        canonical_headers = "".join(
            f"{k}:{headers_to_sign[k]}\n" for k in sorted(headers_to_sign.keys())
        )
        canonical_request = f"{method}\n{uri}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

        # String to sign
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.aws_region}/{self.service}/aws4_request"
        string_to_sign = (
            f"{algorithm}\n{amz_date}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        # Signature
        signing_key = self._get_signature_key(date_stamp)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # Authorization header
        auth_header = (
            f"{algorithm} Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers = {
            **headers_to_sign,
            "Authorization": auth_header,
        }

        response = requests.post(f"https://{self.host}{uri}", headers=headers, data=body)

        if not response.ok:
            error_info = response.json() if response.text else {"status": response.status_code}
            print(f"API Error: {json.dumps(error_info, indent=2)}")
            return {}

        return response.json()

    def get_items(self, asins: list[str]) -> list[dict]:
        """Get product info by ASIN(s)."""
        payload = {
            "ItemIds": asins,
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Resources": [
                "ItemInfo.Title",
                "ItemInfo.ByLineInfo",
                "ItemInfo.Features",
                "Offers.Listings.Price",
                "Images.Primary.Large",
                "BrowseNodeInfo.BrowseNodes",
            ],
        }

        result = self._make_request("GetItems", payload)
        return result.get("ItemsResult", {}).get("Items", [])

    def search_items(self, keywords: str, category: str = "All", max_results: int = 10) -> list[dict]:
        """Search for products by keyword."""
        payload = {
            "Keywords": keywords,
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "SearchIndex": category,
            "ItemCount": min(max_results, 10),
            "Resources": [
                "ItemInfo.Title",
                "ItemInfo.ByLineInfo",
                "Offers.Listings.Price",
                "Images.Primary.Medium",
            ],
        }

        result = self._make_request("SearchItems", payload)
        return result.get("SearchResult", {}).get("Items", [])

    def get_affiliate_link(self, asin: str) -> str:
        """Generate affiliate link for an ASIN."""
        return f"https://www.amazon.com/dp/{asin}?tag={self.partner_tag}"

    def get_product_info(self, asin: str) -> dict | None:
        """Get detailed product info including affiliate link."""
        items = self.get_items([asin])
        if not items:
            return None

        item = items[0]
        info = {
            "asin": item.get("ASIN"),
            "title": item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", "N/A"),
            "affiliate_link": self.get_affiliate_link(item.get("ASIN")),
            "detail_url": item.get("DetailPageURL"),
        }

        # Price
        offers = item.get("Offers", {}).get("Listings", [])
        if offers:
            price = offers[0].get("Price", {})
            info["price"] = price.get("DisplayAmount", "N/A")
            info["price_value"] = price.get("Amount")

        # Brand/Author
        byline = item.get("ItemInfo", {}).get("ByLineInfo", {})
        if byline.get("Brand"):
            info["brand"] = byline["Brand"].get("DisplayValue")
        if byline.get("Manufacturer"):
            info["manufacturer"] = byline["Manufacturer"].get("DisplayValue")

        # Image
        images = item.get("Images", {}).get("Primary", {})
        if images.get("Large"):
            info["image_url"] = images["Large"].get("URL")

        # Features
        features = item.get("ItemInfo", {}).get("Features", {}).get("DisplayValues", [])
        if features:
            info["features"] = features[:5]

        return info


def print_product(product: dict):
    """Print product info in formatted output."""
    print(f"\n{'=' * 60}")
    print(f"Title: {product.get('title', 'N/A')}")
    print(f"ASIN: {product.get('asin', 'N/A')}")
    if product.get("brand"):
        print(f"Brand: {product['brand']}")
    if product.get("price"):
        print(f"Price: {product['price']}")
    print(f"\nAffiliate Link:\n  {product.get('affiliate_link', 'N/A')}")
    if product.get("image_url"):
        print(f"\nImage: {product['image_url']}")
    if product.get("features"):
        print("\nFeatures:")
        for f in product["features"][:3]:
            print(f"  - {f[:80]}...")


def print_search_results(items: list[dict], partner_tag: str):
    """Print search results."""
    if not items:
        print("No products found.")
        return

    print(f"\nFound {len(items)} products:\n")
    for i, item in enumerate(items, 1):
        asin = item.get("ASIN", "N/A")
        title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", "N/A")
        price = "N/A"
        offers = item.get("Offers", {}).get("Listings", [])
        if offers:
            price = offers[0].get("Price", {}).get("DisplayAmount", "N/A")

        print(f"{i}. {title[:60]}")
        print(f"   ASIN: {asin} | Price: {price}")
        print(f"   Link: https://www.amazon.com/dp/{asin}?tag={partner_tag}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Amazon Affiliate Tool - fetch product info and affiliate links",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Get affiliate link for a product:
    python amazon_affiliate.py get B0BSHF7WHW

  Search for products:
    python amazon_affiliate.py search "wireless earbuds"

  Search in specific category:
    python amazon_affiliate.py search "cookbook" --category Books

  Output as JSON:
    python amazon_affiliate.py get B0BSHF7WHW --json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get product info by ASIN")
    get_parser.add_argument("asin", help="Product ASIN (e.g., B0BSHF7WHW)")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for products")
    search_parser.add_argument("keywords", help="Search keywords")
    search_parser.add_argument(
        "--category",
        default="All",
        help="Search category (default: All). Options: All, Electronics, Books, Kitchen, etc.",
    )
    search_parser.add_argument(
        "--max", type=int, default=5, help="Max results (default: 5, max: 10)"
    )
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Link command (quick affiliate link without API call)
    link_parser = subparsers.add_parser("link", help="Generate affiliate link (no API call)")
    link_parser.add_argument("asin", help="Product ASIN")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    creds = load_credentials()
    client = AmazonAffiliate(
        access_key=creds["access_key"],
        secret_key=creds["secret_key"],
        partner_tag=creds["partner_tag"],
        region=creds.get("region", "us"),
    )

    if args.command == "get":
        product = client.get_product_info(args.asin)
        if product:
            if args.json:
                print(json.dumps(product, indent=2))
            else:
                print_product(product)
        else:
            print(f"Product not found: {args.asin}")
            sys.exit(1)

    elif args.command == "search":
        items = client.search_items(args.keywords, args.category, args.max)
        if args.json:
            results = []
            for item in items:
                asin = item.get("ASIN")
                results.append({
                    "asin": asin,
                    "title": item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue"),
                    "price": item.get("Offers", {}).get("Listings", [{}])[0].get("Price", {}).get("DisplayAmount"),
                    "affiliate_link": client.get_affiliate_link(asin),
                })
            print(json.dumps(results, indent=2))
        else:
            print_search_results(items, creds["partner_tag"])

    elif args.command == "link":
        link = client.get_affiliate_link(args.asin)
        print(f"Affiliate link for {args.asin}:")
        print(f"  {link}")


if __name__ == "__main__":
    main()
