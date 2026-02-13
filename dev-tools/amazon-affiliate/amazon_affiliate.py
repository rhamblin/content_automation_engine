"""Amazon Affiliate Tool - fetch affiliate links and product info via Creators API."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Add bundled SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "creatorsapi-python-sdk"))

from creatorsapi_python_sdk.api_client import ApiClient
from creatorsapi_python_sdk.models.get_items_request_content import (
    GetItemsRequestContent,
)
from creatorsapi_python_sdk.models.search_items_request_content import (
    SearchItemsRequestContent,
)

from creatorsapi_python_sdk.api.default_api import DefaultApi

# Regex patterns for extracting ASIN from Amazon URLs
ASIN_PATTERNS = [
    r"/dp/([A-Z0-9]{10})",
    r"/gp/product/([A-Z0-9]{10})",
    r"[?&]asin=([A-Z0-9]{10})",
]


def load_credentials() -> dict:
    """Load Amazon Creators API credentials from file."""
    creds_path = Path(__file__).parent / "amazon-credentials.json"
    if not creds_path.exists():
        print(f"Error: Credentials file not found at {creds_path}")
        print("Create amazon-credentials.json with:")
        print(
            json.dumps(
                {
                    "credential_id": "YOUR_CREDENTIAL_ID",
                    "credential_secret": "YOUR_CREDENTIAL_SECRET",
                    "partner_tag": "YOUR_TAG-20",
                },
                indent=2,
            )
        )
        sys.exit(1)
    return json.loads(creds_path.read_text())


def extract_asin(url: str) -> str | None:
    """Extract ASIN from an Amazon product URL."""
    for pattern in ASIN_PATTERNS:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def get_image_url(item) -> str | None:
    """Extract best available image URL from an item."""
    if not item.images or not item.images.primary:
        return None
    primary = item.images.primary
    for size in (primary.large, primary.medium, primary.small):
        if size and size.url:
            return size.url
    return None


class AmazonAffiliate:
    """Amazon Creators API client."""

    def __init__(
        self,
        credential_id: str,
        credential_secret: str,
        partner_tag: str,
        version: str = "2.1",
        marketplace: str = "www.amazon.com",
    ):
        self.partner_tag = partner_tag
        self.marketplace = marketplace
        api_client = ApiClient(
            credential_id=credential_id,
            credential_secret=credential_secret,
            version=version,
        )
        self.api = DefaultApi(api_client)

    def get_items(self, asins: list[str]) -> list:
        """Get product info by ASIN(s)."""
        request = GetItemsRequestContent(
            partner_tag=self.partner_tag,
            item_ids=asins,
            resources=[
                "images.primary.large",
                "itemInfo.title",
                "itemInfo.features",
                "itemInfo.byLineInfo",
                "offersV2.listings.price",
            ],
        )
        response = self.api.get_items(
            x_marketplace=self.marketplace,
            get_items_request_content=request,
        )
        if response.items_result and response.items_result.items:
            return response.items_result.items
        return []

    def search_items(
        self, keywords: str, category: str = "All", max_results: int = 10
    ) -> list:
        """Search for products by keyword."""
        request = SearchItemsRequestContent(
            partner_tag=self.partner_tag,
            keywords=keywords,
            search_index=category,
            item_count=min(max_results, 100),
            resources=[
                "images.primary.medium",
                "itemInfo.title",
                "offersV2.listings.price",
            ],
        )
        response = self.api.search_items(
            x_marketplace=self.marketplace,
            search_items_request_content=request,
        )
        if response.search_result and response.search_result.items:
            return response.search_result.items
        return []

    def get_affiliate_link(self, asin: str) -> str:
        """Generate affiliate link for an ASIN."""
        return f"https://www.amazon.com/dp/{asin}?tag={self.partner_tag}"

    def get_product_info(self, asin: str) -> dict | None:
        """Get detailed product info including affiliate link and image URL."""
        items = self.get_items([asin])
        if not items:
            return None
        return self._parse_item(items[0])

    def _parse_item(self, item) -> dict:
        """Parse an SDK Item object into a plain dict."""
        info = {
            "asin": item.asin,
            "title": "N/A",
            "affiliate_link": self.get_affiliate_link(item.asin),
            "detail_url": item.detail_page_url,
            "image_url": get_image_url(item),
        }

        if item.item_info:
            if item.item_info.title and item.item_info.title.display_value:
                info["title"] = item.item_info.title.display_value

            by_line = item.item_info.by_line_info
            if by_line:
                if hasattr(by_line, "brand") and by_line.brand:
                    info["brand"] = (
                        by_line.brand.display_value
                        if hasattr(by_line.brand, "display_value")
                        else str(by_line.brand)
                    )
                if hasattr(by_line, "manufacturer") and by_line.manufacturer:
                    info["manufacturer"] = (
                        by_line.manufacturer.display_value
                        if hasattr(by_line.manufacturer, "display_value")
                        else str(by_line.manufacturer)
                    )

            if item.item_info.features and item.item_info.features.display_values:
                info["features"] = item.item_info.features.display_values[:5]

        if item.offers_v2 and item.offers_v2.listings:
            listing = item.offers_v2.listings[0]
            if listing.price and listing.price.money:
                info["price"] = listing.price.money.display_amount
                info["price_value"] = listing.price.money.amount

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


def print_search_results(items: list, partner_tag: str):
    """Print search results."""
    if not items:
        print("No products found.")
        return

    print(f"\nFound {len(items)} products:\n")
    for i, item in enumerate(items, 1):
        asin = item.asin or "N/A"
        title = "N/A"
        if item.item_info and item.item_info.title:
            title = item.item_info.title.display_value or "N/A"
        price = "N/A"
        if item.offers_v2 and item.offers_v2.listings:
            listing = item.offers_v2.listings[0]
            if listing.price and listing.price.money:
                price = listing.price.money.display_amount or "N/A"
        image_url = get_image_url(item) or ""

        print(f"{i}. {title[:60]}")
        print(f"   ASIN: {asin} | Price: {price}")
        print(f"   Link: https://www.amazon.com/dp/{asin}?tag={partner_tag}")
        if image_url:
            print(f"   Image: {image_url}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Amazon Affiliate Tool - fetch product info and affiliate links via Creators API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Get affiliate link for a product:
    python amazon_affiliate.py get B0BSHF7WHW

  Get product info from Amazon URL:
    python amazon_affiliate.py url "https://www.amazon.com/dp/B0BSHF7WHW"

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

    # URL command
    url_parser = subparsers.add_parser("url", help="Get product info from Amazon URL")
    url_parser.add_argument("product_url", help="Amazon product URL")
    url_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for products")
    search_parser.add_argument("keywords", help="Search keywords")
    search_parser.add_argument(
        "--category",
        default="All",
        help="Search category (default: All). Options: All, Electronics, Books, Kitchen, etc.",
    )
    search_parser.add_argument(
        "--max", type=int, default=5, help="Max results (default: 5, max: 100)"
    )
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Link command (quick affiliate link without API call)
    link_parser = subparsers.add_parser(
        "link", help="Generate affiliate link (no API call)"
    )
    link_parser.add_argument("asin", help="Product ASIN")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    creds = load_credentials()

    # Link command doesn't need API auth
    if args.command == "link":
        tag = creds.get("partner_tag", "")
        link = f"https://www.amazon.com/dp/{args.asin}?tag={tag}"
        print(f"Affiliate link for {args.asin}:")
        print(f"  {link}")
        return

    client = AmazonAffiliate(
        credential_id=creds["credential_id"],
        credential_secret=creds["credential_secret"],
        partner_tag=creds["partner_tag"],
        version=creds.get("version", "2.1"),
        marketplace=creds.get("marketplace", "www.amazon.com"),
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

    elif args.command == "url":
        asin = extract_asin(args.product_url)
        if not asin:
            print(f"Error: Could not extract ASIN from URL: {args.product_url}")
            sys.exit(1)
        product = client.get_product_info(asin)
        if product:
            if args.json:
                print(json.dumps(product, indent=2))
            else:
                print_product(product)
        else:
            print(f"Product not found: {asin}")
            sys.exit(1)

    elif args.command == "search":
        items = client.search_items(args.keywords, args.category, args.max)
        if args.json:
            results = []
            for item in items:
                results.append(client._parse_item(item))
            print(json.dumps(results, indent=2))
        else:
            print_search_results(items, creds["partner_tag"])


if __name__ == "__main__":
    main()
