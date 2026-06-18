
import csv
import sqlite3
import os
from database import init_db, DB

CSV_PATH = "amazon.csv"   # ← change this if your file has a different name


def clean_price(value: str) -> float:
    """Remove ₹, $, commas and convert to float."""
    if not value:
        return 0.0
    return float(value.replace("₹", "").replace("$", "").replace(",", "").strip())


def clean_percentage(value: str) -> float:
    """Remove % and convert to float."""
    if not value:
        return 0.0
    return float(value.replace("%", "").strip())


def clean_rating(value: str) -> float:
    if not value:
        return 0.0
    try:
        return float(value.strip())
    except ValueError:
        return 0.0


def clean_rating_count(value: str) -> int:
    if not value:
        return 0
    try:
        return int(value.replace(",", "").strip())
    except ValueError:
        return 0


def load():
    if not os.path.exists(CSV_PATH):
        print(f"❌ File not found: {CSV_PATH}")
        print("   Place your CSV in the same folder and update CSV_PATH in load_data.py")
        return

    init_db()

    products_inserted = 0
    reviews_inserted  = 0
    skipped           = 0

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        # Clear existing data
        cursor.execute("DELETE FROM reviews")
        cursor.execute("DELETE FROM products")
        conn.commit()

        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                product_id = row.get("product_id", "").strip()
                if not product_id:
                    skipped += 1
                    continue

                # ── Insert product (ignore duplicates) ────────────────────────
                cursor.execute("""
                    INSERT OR IGNORE INTO products
                        (product_id, product_name, category,
                         discounted_price, actual_price, discount_percentage,
                         rating, rating_count, about_product, img_link, product_link)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id,
                    row.get("product_name", "").strip(),
                    row.get("category", "").strip(),
                    clean_price(row.get("discounted_price", "")),
                    clean_price(row.get("actual_price", "")),
                    clean_percentage(row.get("discount_percentage", "")),
                    clean_rating(row.get("rating", "")),
                    clean_rating_count(row.get("rating_count", "")),
                    row.get("about_product", "").strip(),
                    row.get("img_link", "").strip(),
                    row.get("product_link", "").strip(),
                ))
                if cursor.rowcount:
                    products_inserted += 1

                review_id = row.get("review_id", "").strip()
                if review_id:
                    cursor.execute("""
                        INSERT OR IGNORE INTO reviews
                            (review_id, product_id, user_id, user_name,
                             review_title, review_content)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        review_id,
                        product_id,
                        row.get("user_id", "").strip(),
                        row.get("user_name", "").strip(),
                        row.get("review_title", "").strip(),
                        row.get("review_content", "").strip(),
                    ))
                    if cursor.rowcount:
                        reviews_inserted += 1

        conn.commit()

    print("✅ Data loaded successfully.")
    print(f"   Products : {products_inserted}")
    print(f"   Reviews  : {reviews_inserted}")
    print(f"   Skipped  : {skipped} rows (missing product_id)")


if __name__ == "__main__":
    load()
