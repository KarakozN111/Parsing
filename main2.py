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

category_pages = {
    'https://halykmarket.kz/category/holodilniki?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung': 17,
    'https://halykmarket.kz/category/morozilniki?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung': 1,
    'https://halykmarket.kz/category/konditsioneri?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':14,
    'https://halykmarket.kz/category/televizori?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':43,
    'https://halykmarket.kz/category/stiralnie-mashini':101,
    'https://halykmarket.kz/category/sushilnie-avtomati?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':1,
    'https://halykmarket.kz/category/parovye-shkafy?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':1,
    'https://halykmarket.kz/category/saundbari':8,
    'https://halykmarket.kz/category/akusticheskie-sistemi?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':1, 
    'https://halykmarket.kz/category/muzikalnie-tsentri?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':2,
    'https://halykmarket.kz/category/portativnyye-kolonki?sort=popular-desc&f=brands%3ALG':1,
    'https://halykmarket.kz/category/monitori?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':20,
    'https://halykmarket.kz/category/mikrovolnovie-pechi?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':6,
    'https://halykmarket.kz/category/pilesosi?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':11,
    'https://halykmarket.kz/category/posudomoechnie-mashini?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':1,
    'https://halykmarket.kz/category/proektori?sort=popular-desc&f=brands%3ALG%3Abrands%3ASamsung':1
}

products_data = []

try:
    for base_url, max_pages in category_pages.items():
        page = 1
        while page <= max_pages:
            url = f"{base_url}&page={page}"
            print(f"\nParsing page {page} of {max_pages}:\n{url}")

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
                    print(f"Still no products. Skipping page {page}.")
                    page += 1
                    continue

            product_links = []
            for idx, product in enumerate(products, start=1):
                try:
                    title = product.find_element(By.CSS_SELECTOR, '.h-product-card__title').text.strip()
                    main_price = product.find_element(By.CSS_SELECTOR, '.h-product-card__price').text
                    link = product.get_attribute("href")
                    if link and title:
                        product_links.append((title, main_price, link, idx))
                except Exception as e:
                    print("Product parsing error:", e)
                    continue

            for title, main_price, link, idx in product_links:
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
                        brand = "Samsung" if "Samsung" in title else "LG" if "LG" in title else "Unknown"
                        products_data.append({
                            "Item": title, "Seller": "No sellers (timeout)", "Price": main_price,
                            "Link": link, "Category": category, "Brand": brand,
                            "Page": page, "Index": idx
                        })
                        continue

                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(0.7, 0.9))

                    raw_category = urlparse(link).path.split("/")[2] if len(urlparse(link).path.split("/")) > 2 else "Unknown"
                    category = category_mapping.get(raw_category, raw_category)
                    brand = "Samsung" if "Samsung" in title else "LG" if "LG" in title else "Unknown"

                    seller_blocks = driver.find_elements(By.CSS_SELECTOR, ".product-merchant__content")
                    if not seller_blocks:
                        products_data.append({
                            "Item": title, "Seller": "No sellers (empty)", "Price": main_price,
                            "Link": link, "Category": category, "Brand": brand,
                            "Page": page, "Index": idx
                        })
                        continue

                    for seller in seller_blocks:
                        try:
                            seller_name = seller.find_element(By.CSS_SELECTOR, ".product-merchant__name").text
                            seller_price = seller.find_element(By.CSS_SELECTOR, ".product-merchant__price").text
                            products_data.append({
                                "Item": title, "Seller": seller_name, "Price": seller_price,
                                "Link": link, "Category": category, "Brand": brand,
                                "Page": page, "Index": idx
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

except KeyboardInterrupt:
    print("\nstoped by user! saving data")
finally:
    driver.quit()

    if products_data:
        df = pd.DataFrame(products_data, columns=["Item", "Seller", "Price", "Link", "Category", "Brand", "Page", "Index"])
        df['Price'] = df["Price"].apply(lambda x: int(''.join(re.findall(r'\d+', x))) if isinstance(x, str) and re.findall(r'\d+', x) else None)
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
                brand TEXT,
                page INTEGER,
                card_index INTEGER,
                parsed_date TEXT
            )
        """)

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO lg_products (name, seller, price, link, category, brand, page, card_index, parsed_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["Item"], row["Seller"], row["Price"], row["Link"], row["Category"],
                row["Brand"], row["Page"], row["Index"], row["Parsed Date"]
            ))

        conn.commit()
        conn.close()

        print(f"\ndone, overall pages: {len(df)}")
    else:
        print("no data to save.")
