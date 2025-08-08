#parser for just product informations from only lg market
from selenium import webdriver #selenium is for automatization of browser(immitates person's behaviour)
from selenium.webdriver.common.by import By #By allows choosing elements by a page (css, xpath, id and so on)
import pandas as pd #pandas for storing and savingdata in excel table
import time # for making pauses between actions
from selenium.webdriver.chrome.options import Options #for configuration browser "chrome"

# turns chrome browser with the given parameters 
options = Options()
options.add_experimental_option('excludeSwitches', ['enable-logging']) # turns off unnecessary log-messages from chrome
driver = webdriver.Chrome(options=options)

base_url = "https://halykmarket.kz/category/tehnika-dlya-doma?sort=popular-desc&f=brands%3ALG"

# list for data about items
products_data = []

# parsing starts from the 1st page
page = 1

#opens items page
while True:
    print(f" Parsing the page {page}...")
    driver.get(base_url + str(page))
    time.sleep(3)

    # scrolling page 3 times so that "lazy" items downloaded properly
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    #finding items with .h-product-card
    products = driver.find_elements(By.CSS_SELECTOR, ".h-product-card")
    if not products:
        print("Items are not found. Stopping.")
        break

    #processing each product(then getting title, main price, link)
    for product in products:
        try:
            title = product.find_element(By.CSS_SELECTOR, ".h-product-card__title").text
            main_price = product.find_element(By.CSS_SELECTOR, ".h-product-card__price").text
            link = product.get_attribute("href")

            print(f"Processing an item: {title}")

            # Переход на страницу товара
            driver.get(link)
            time.sleep(3)

            #scolling pages for sellers
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)

            # Сбор продавцов
            sellers = []
            seller_blocks = driver.find_elements(By.CSS_SELECTOR, ".product-merchant__content")

            for seller in seller_blocks:
                try:
                    seller_name = seller.find_element(By.CSS_SELECTOR, ".product-merchant__name").text
                    seller_price = seller.find_element(By.CSS_SELECTOR, ".product-merchant__price").text
                    sellers.append((seller_name, seller_price))
                except:
                    continue

            # creating dictionary for data
            product_info = {
                "Title": title,
                "Main Price": main_price,
                "Link": link
            }
            for i, (s_name, s_price) in enumerate(sellers, start=1):
                product_info[f"Seller {i}"] = s_name
                product_info[f"Price {i}"] = s_price
            products_data.append(product_info)

            # getting back to items list
            driver.back()
            time.sleep(2)

        except Exception as e:
            print("Error:", e)
            continue
        #getting new page
    page += 1

driver.quit()

# saving in .Excel
df = pd.DataFrame(products_data)
df.to_excel("lg_products_with_sellers.xlsx", index=False)
print(f"Done! Overall saved: {len(products_data)}")