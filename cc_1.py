# old data + new data, убрала точные цифры страниц, точное время, вместо дикшнри заменила листом для 
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from selenium import webdriver
from datetime import datetime
import pandas as pd
import sqlite3
import random
import time
import re
import os
category_mapping = {
    "holodilniki": "REF",
    "morozilniki": "REF",
    "konditsioneri": "RAC",
    "televizori": "TV",
    "stiralnie-mashini": "WM",
    "sushilnie-avtomati": "WM",
    "parovye-shkafy": "Styler",
    "saundbari": "CAV",
    "akusticheskie-sistemi": "CAV",
    "muzikalnie-tsentri": "CAV",
    "portativnyye-kolonki": "CAV",
    "monitori": "MNT",
    "mikrovolnovie-pechi": "MWO",
    "pilesosi": "VC",
    "posudomoechnie-mashini": "DW",
    "proektori": "Projectors"
}


options = Options()
options.headless = False
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(options=options)


category_urls = [
    'https://halykmarket.kz/category/tehnika-dlya-doma?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung',
    'https://halykmarket.kz/category/noutbuki-i-kompyuteri?sort=popular-desc&f=brands%3ASamsung%3Abrands%3ALG',
    'https://halykmarket.kz/category/kuhonnaya-tehnika?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung',
    'https://halykmarket.kz/category/televizori-i-audiotehnika?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung'
]

def get_total_pages(driver, url):
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        pages = driver.find_elements(By.CSS_SELECTOR, "ul.pagination li.page-item a")
        page_numbers = [int(p.text) for p in pages if p.text.isdigit()]
        return max(page_numbers) if page_numbers else 1
    except:
        return 1

products_data = []

for base_url in category_urls:
    total_pages = get_total_pages(driver, base_url)
    print(f"\n➡ Обнаружено страниц: {total_pages} для URL: {base_url}")
    page = 1

    while page <= total_pages:
        url = f"{base_url}&page={page}"
        print(f"\nParsing page {page} of {total_pages}:\n{url}")

        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                lambda d: any(
                    card.find_element(By.CSS_SELECTOR, '.h-product-card__title').text.strip()
                    for card in d.find_elements(By.CSS_SELECTOR, '.h-product-card')
                    if card.is_displayed()
                )
            )
            time.sleep(random.uniform(0.7, 0.9))
        except Exception as e:
            print(f"Error loading page {url}: {e}")
            page += 1
            continue

        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(0.7, 0.9))
        except Exception as e:
            print("Scroll error:", e)

        products = driver.find_elements(By.CSS_SELECTOR, ".h-product-card")
        if not products:
            print(f"No products found on page {page}. Retrying once...")
            time.sleep(0.9)
            try:
                driver.get(url)
                WebDriverWait(driver, 20).until(
                    lambda d: any(
                        card.find_element(By.CSS_SELECTOR, '.h-product-card__title').text.strip()
                        for card in d.find_elements(By.CSS_SELECTOR, '.h-product-card')
                        if card.is_displayed()
                    )
                )
                products = driver.find_elements(By.CSS_SELECTOR, ".h-product-card")
            except:
                print(f"⏭ Still no products. Skipping page {page}.")
                page += 1
                continue

        product_links = []
        for product in products:
            try:
                title = product.find_element(By.CSS_SELECTOR, '.h-product-card__title').text.strip()
                main_price = product.find_element(By.CSS_SELECTOR, '.h-product-card__price').text
                link = product.get_attribute("href")
                if link and title:
                    product_links.append((title, main_price, link))
                else:
                    print("Пропуск товара: пустой title или ссылка")
            except Exception as e:
                print("Product parsing error:", e)
                continue

        for title, main_price, link in product_links:
            print(f"Processing item: {title}")
            try:
                driver.get(link)

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-merchant__content"))
                    )
                except TimeoutException:
                    print(f"Timeout while waiting for seller content at {link}")
                    raw_category = urlparse(link).path.split("/")[2] if len(urlparse(link).path.split("/")) > 2 else "Unknown"
                    category = category_mapping.get(raw_category, raw_category)
                    products_data.append({
                        "Item": title,
                        "Seller": "No sellers (timeout)",
                        "Price": main_price,
                        "Link": link,
                        "Category": category
                    })
                    continue

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(0.7, 0.9))

                raw_category = urlparse(link).path.split("/")[2] if len(urlparse(link).path.split("/")) > 2 else "Unknown"
                category = category_mapping.get(raw_category, raw_category)

                seller_blocks = driver.find_elements(By.CSS_SELECTOR, ".product-merchant__content")
                if not seller_blocks:
                    products_data.append({
                        "Item": title,
                        "Seller": "No sellers (empty)",
                        "Price": main_price,
                        "Link": link,
                        "Category": category
                    })
                    continue

                for seller in seller_blocks:
                    try:
                        seller_name = seller.find_element(By.CSS_SELECTOR, ".product-merchant__name").text
                        seller_price = seller.find_element(By.CSS_SELECTOR, ".product-merchant__price").text
                        products_data.append({
                            "Item": title,
                            "Seller": seller_name,
                            "Price": seller_price,
                            "Link": link,
                            "Category": category
                        })
                    except StaleElementReferenceException:
                        print("Stale element in seller block, skipping seller.")
                    except Exception as e:
                        print(f"Unexpected error in seller block: {e}")
                        continue

            except Exception as e:
                print(f"Error while processing item '{title}': {e}")
                continue
        page += 1

driver.quit()

df = pd.DataFrame(products_data, columns=["Item", "Seller", "Price", "Link", "Category"])
df['Price'] = df["Price"].apply(lambda x: int(''.join(re.findall(r'\d+', x))) if isinstance(x, str) else None)
df["Parsed Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

excel_file = 'lg_products_with_category_and_chars.xlsx'
if os.path.exists(excel_file):
    existing_df = pd.read_excel(excel_file)
    df = pd.concat([existing_df, df], ignore_index=True)

df.to_excel(excel_file, index=False)
print(f'\n Excel is updated: {len(df)} rows in file')

conn = sqlite3.connect("products.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS lg_products (
        name TEXT,
        seller TEXT,
        price INTEGER,
        link TEXT,
        category TEXT,
        parsed_date TEXT
    )
""")

for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO lg_products (name, seller, price, link, category, parsed_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        row["Item"],
        row["Seller"],
        row["Price"],
        row["Link"],
        row["Category"],
        row["Parsed Date"]
    ))

conn.commit()
conn.close()

print(f"\nDone. Total saved rows: {len(products_data)}")


