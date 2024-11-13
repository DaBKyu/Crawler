from utils import *
from selenium.webdriver.common.by import By

driver_path = 'C:\\Users\\gladius\\Desktop\\Crawl\\chromedriver-win64\\chromedriver.exe'

def crawlItems(elements, subDriver, query):
    items = []
    for e in elements:
        # 제품 이름
        productName = e.find_element(By.NAME, "productName").text

        # 제품 설명
        prdoctuInfo = ""
        productInfos = e.find_element(By.CLASS_NAME, "spec_list")

        for s in productInfos:
            if s.

        # 둥록 일자
        registedDate = e.find_element(By.XPATH, "//div/div/div[2]/div[5]/span[1]").text[4:]
        
        # 가격
        try: 
            price = e.find_element(By.CLASS_NAME, "price_num__S2p_v").text
        except:
            price = "판매 중단"
        
        # 배송비
        deliveryFee = e.find_element(By.CLASS_NAME, "price_delivery__yw_We").text.split()[-1]

        # 카테고리
        categories = []
        elementCategories = e.find_elements(By.CLASS_NAME, "product_category__l4FWz.product_nohover__Z0Muw")
        for elementCategory in elementCategories:
            categories.append(elementCategory.text)
        categories = " > ".join(categories)

        # 판매자
        try: 
            sellerElement  = e.find_element(By.CLASS_NAME, "product_mall__hPiEH.linkAnchor")
            if sellerElement.text == "":
                seller= sellerElement.find_element(By.TAG_NAME, "img").get_attribute("alt")
            else:
                seller= sellerElement.text
        except:
            seller = "추가 처리 필요"
        
        item = {
            "search_keyword": query,
            "productName": productName,
            "link": link,
            "price": price,
            "deliveryFee": deliveryFee,
            "registedDate": registedDate,
            "category": categories,
            "seller": seller
            }
        items.append(item)
    return items