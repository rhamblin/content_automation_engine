"""Tests for ASIN extraction from Amazon URLs."""

from amazon_affiliate import extract_asin


def test_dp_url():
    assert extract_asin("https://www.amazon.com/dp/B0BSHF7WHW") == "B0BSHF7WHW"


def test_dp_url_with_slug():
    assert extract_asin("https://www.amazon.com/Some-Product/dp/B0BSHF7WHW/ref=sr_1_1") == "B0BSHF7WHW"


def test_gp_product_url():
    assert extract_asin("https://www.amazon.com/gp/product/B0BSHF7WHW") == "B0BSHF7WHW"


def test_query_param():
    assert extract_asin("https://www.amazon.com/s?asin=B0BSHF7WHW") == "B0BSHF7WHW"


def test_query_param_not_first():
    assert extract_asin("https://www.amazon.com/s?k=test&asin=B0BSHF7WHW") == "B0BSHF7WHW"


def test_lowercase_asin_normalized():
    assert extract_asin("https://www.amazon.com/dp/b0bshf7whw") == "B0BSHF7WHW"


def test_no_asin_returns_none():
    assert extract_asin("https://www.amazon.com/some-random-page") is None


def test_short_id_returns_none():
    assert extract_asin("https://www.amazon.com/dp/B0BSH") is None


if __name__ == "__main__":
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"  PASS  {name}")
    print("\nAll tests passed.")
