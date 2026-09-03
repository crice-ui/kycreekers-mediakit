#!/usr/bin/env python3
"""
update_products.py — Refresh products.json from kycreekers.com

Usage:
    python update_products.py            # refresh products.json from FEATURED list
    python update_products.py --list     # list every product on the shop (for picking slugs)

Edit the FEATURED list below to control which products appear on the landing page.
Each entry needs a `slug` (the part after /product-page/ in the URL).
Optionally override `name` or `category` for nicer display.

No external dependencies — uses only Python's standard library.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

# ============================================================
# EDIT THIS LIST TO CHANGE WHICH PRODUCTS APPEAR ON THE PAGE
# ============================================================
FEATURED = [
    {
        "slug": "880s-garret-wine",
        "name": "1880s Garrett & Co. Wine Bottle",
        "category": "Antique Bottle • North Carolina",
    },
    {
        "slug": "kycreekers-fleece-hoodie-stay-warm-in-style-this-winter",
        "name": "KyCreekers Fleece Hoodie",
        "category": "Apparel • Hoodie",
    },
    {
        "slug": "fulton-ky-hutch",
        "name": "Fulton, KY Hutchinson Soda",
        "category": "Antique Bottle • Fulton, KY",
    },
    {
        "slug": "kycreekers-antique-shop-long-sleeve-tee",
        "name": "KyCreekers Antique Shop Long-Sleeve",
        "category": "Apparel • Long-Sleeve Tee",
    },
    {
        "slug": "early-apothecary-bottles",
        "name": "Early Amber Apothecary Bottles (Pair)",
        "category": "Antique Glass • Apothecary",
    },
    {
        "slug": "snapback-hat-kycreekers-design",
        "name": "KyCreekers Snapback Hat",
        "category": "Apparel • Snapback",
    },
]
# ============================================================

BASE = "https://www.kycreekers.com"
SHOP_URL = f"{BASE}/shop"
OUT_FILE = Path(__file__).parent / "products.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (KyCreekers products updater)",
    "Accept": "text/html,application/xhtml+xml",
}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_image_url(value):
    """Convert any schema.org image value (string, list, or ImageObject dict) into a plain URL."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for v in value:
            url = extract_image_url(v)
            if url:
                return url
        return None
    if isinstance(value, dict):
        return value.get("contentUrl") or value.get("url") or None
    return None


CARD_IMAGE_WIDTH = 800  # display-optimized width for product cards (retina-friendly)


def normalize_wix_image(url):
    """Drop any existing Wix CDN transform and apply our own ~800px fit so cards load fast."""
    if not url:
        return url
    base = url.split("/v1/")[0] if "/v1/" in url else url
    return f"{base}/v1/fit/w_{CARD_IMAGE_WIDTH},h_{CARD_IMAGE_WIDTH},q_85/file.jpg"


def extract_meta(html, prop):
    """Pull a meta property/name value from HTML."""
    pattern = (
        rf'<meta\s+(?:property|name)=["\']{re.escape(prop)}["\']\s+content=["\']([^"\']+)["\']'
    )
    m = re.search(pattern, html, re.IGNORECASE)
    return m.group(1) if m else None


def parse_product_page(html, slug):
    """Extract name, price, image, availability from a product page. Tries JSON-LD then meta tags."""
    name, price, image, availability = None, None, None, None

    # 1) JSON-LD (most reliable on Wix product pages)
    for match in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL,
    ):
        try:
            data = json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            graph = item.get("@graph", [item]) if isinstance(item, dict) else [item]
            for node in graph:
                if not isinstance(node, dict):
                    continue
                if node.get("@type") in ("Product", ["Product"]) or "Product" in str(node.get("@type", "")):
                    name = name or node.get("name")
                    if image is None:
                        image = extract_image_url(node.get("image"))
                    offers = node.get("offers")
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    if isinstance(offers, dict):
                        p = offers.get("price")
                        if p is not None:
                            price = price or str(p)
                        avail = offers.get("availability")
                        if avail and availability is None:
                            availability = str(avail)

    # 2) Fallback: og: tags
    name = name or extract_meta(html, "og:title")
    image = image or extract_meta(html, "og:image")
    if availability is None:
        availability = extract_meta(html, "product:availability") or extract_meta(html, "og:availability")
    # Apply a sensible Wix CDN transform so card images load fast
    image = normalize_wix_image(image)

    # 3) Fallback: price hunt in HTML body
    if not price:
        m = re.search(r"\$(\d{1,4}(?:\.\d{2})?)", html)
        if m:
            price = m.group(1)

    # Normalize price: "20.00" -> "$20", "29.95" -> "$29.95"
    if price:
        price = str(price).replace("$", "").strip()
        try:
            num = float(price)
            price = f"${int(num)}" if num.is_integer() else f"${num:.2f}"
        except ValueError:
            price = f"${price}"

    # Fallback name from slug if all else fails
    if not name:
        name = slug.replace("-", " ").title()

    return {
        "name": name,
        "price": price or "",
        "image": image or "",
        "availability": availability or "",
    }


def list_all_shop_products():
    """Print every product slug + name + price found on /shop."""
    print(f"Fetching {SHOP_URL} ...")
    html = fetch(SHOP_URL)
    slugs = sorted(set(re.findall(r"/product-page/([a-z0-9\-]+)", html)))
    print(f"\nFound {len(slugs)} products:\n")
    for slug in slugs:
        print(f"  · {slug}")
    print()
    return slugs


def is_in_stock(availability):
    """Return True unless availability clearly says out of stock / discontinued / sold out."""
    if not availability:
        return True  # if we can't tell, default to showing the product
    s = str(availability).lower()
    bad_signals = ("outofstock", "out_of_stock", "out of stock",
                   "discontinued", "soldout", "sold out")
    return not any(sig in s for sig in bad_signals)


def refresh():
    print(f"Refreshing products.json from {BASE} ({len(FEATURED)} featured)...\n")
    out = []
    skipped = []
    for entry in FEATURED:
        slug = entry["slug"]
        url = f"{BASE}/product-page/{slug}"
        print(f"  · {slug}", end="")
        try:
            html = fetch(url)
            parsed = parse_product_page(html, slug)
            if not is_in_stock(parsed["availability"]):
                print("  [SKIPPED — out of stock]")
                skipped.append(slug)
                continue
            print()
            out.append({
                "name": entry.get("name") or parsed["name"],
                "category": entry.get("category", "Item"),
                "price": parsed["price"],
                "image": parsed["image"],
                "url": url,
            })
        except Exception as e:
            print(f"  [SKIPPED — {e}]")
            skipped.append(slug)

    payload = {"featured": out, "catalog_url": SHOP_URL}
    OUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {len(out)} products to {OUT_FILE.name}")
    if skipped:
        print(f"Skipped {len(skipped)} out-of-stock: {', '.join(skipped)}")


def main():
    if "--list" in sys.argv:
        list_all_shop_products()
    else:
        refresh()


if __name__ == "__main__":
    main()
