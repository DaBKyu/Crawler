import os
import re
import time
import requests
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from PIL import Image
from io import BytesIO

from utils import *
 
driver_path = 'C:\\Users\\gladius\\Desktop\\Crawl\\chromedriver-win64\\chromedriver.exe'
 
start_time = time.time()
#shopping = setupBeforeCrawling(chromeDriver=driver)

service = webdriver.ChromeService(executable_path=driver_path)
options = Options()
options.add_argument("--start-maximized") # 화면 최대화
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
options.add_argument("accept-language=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
options.add_experimental_option("detach", True)
driver = webdriver.Chrome(service=service, options=options)

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win64",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

# 경로 설정
images_dir = "images"
if not os.path.exists(images_dir):
    os.makedirs(images_dir)
 
# 다나와 메인 페이지 이동
driver.get("https://www.danawa.com/")
print("크롬 드라이버 현재 URL: " + driver.current_url)
print("크롬 드라이버 현재 URL Title: " + driver.title)

# 로딩 대기
driver.implicitly_wait(5)
 
search = driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div[1]/form/fieldset/div[1]/input[1]")
search.click()

crawledItems = []
search.send_keys("스피커")
search.send_keys(Keys.ENTER)

#subDriver = chrome_driver(driver_path, headless=True)
print("크롬 드라이버 현재 URL: " + driver.current_url)
print("크롬 드라이버 현재 URL Title: " + driver.title)
print("===========[{}] 데이터를 수집합니다.".format("스피커"))

time.sleep(4)

# 리스트 페이지 핸들을 저장
list_page_handle = driver.current_window_handle

# 상품 리스트 불러오기
itemList = driver.find_element(By.CLASS_NAME, "main_prodlist")
all_items = itemList.find_elements(By.CLASS_NAME, "prod_item")
items = [item for item in all_items if re.match(r"^productItem\d+", item.get_attribute("id"))]

for i in items:

    #상품 이름
    productName = i.find_element(By.CLASS_NAME, "prod_name ").find_element(By.TAG_NAME, "a")
    print(productName.text)
    
    #상품 가격
    priceText = i.find_element(By.CLASS_NAME, "price_sect").find_element(By.TAG_NAME, "a").text
    price = re.sub(r'\D', '', priceText)
    print(price)

    #상품 이름 클릭후 이동(상품 가격 리스트 페이지)
    time.sleep(random.uniform(3, 6))
    productName.click()
    time.sleep(random.uniform(3, 6))
    window_handle = driver.window_handles[-1]
    driver.switch_to.window(window_handle)

    #최저가 사러가기 버튼 클릭 후 이동(상품 상세페이지)
    button = driver.find_element(By.CLASS_NAME, "buy_link")
    button.click()
    time.sleep(random.uniform(6, 10))
    window_handle = driver.window_handles[-1]
    driver.switch_to.window(window_handle)

    #현재 위치 출력
    print("크롬 드라이버 현재 URL: " + driver.current_url)
    print("크롬 드라이버 현재 URL Title: " + driver.title)
    
    #url 구분
    if re.match(r"^https://item\.gmarket", driver.current_url):
        print("G마켓")
    elif re.match(r"^http://itempage3\.auction", driver.current_url):
        print("Auction")
        
        #썸네일
        thumbnail_elements = driver.find_elements(By.CSS_SELECTOR, "ul.viewer img")

        for idx, img in enumerate(thumbnail_elements):
            time.sleep(random.uniform(2, 5))
            img_url = img.get_attribute("src")
            if img_url.startswith("//"):  # URL이 //로 시작하면 http 추가
                img_url = "https:" + img_url

            # 이미지 요청
            response = requests.get(img_url)
            response.raise_for_status()  # 요청이 실패하면 예외 발생

            # Pillow를 사용하여 이미지를 열고 저장
            image = Image.open(BytesIO(response.content))

            # 썸네일 다운로드
            if response.status_code == 200:
                file_extension = image.format.lower()  # 'jpeg', 'png' 등의 형식 반환
                file_path = os.path.join(images_dir, f"{productName.text}_thumbnail_{idx + 1}.{file_extension}")
                image.save(file_path)
                print(f"Downloaded {file_path}")

        #제품 정보 사진
        #iframe으로 이동
        iframe = driver.find_element(By.ID, "hIfrmExplainView")
        driver.switch_to.frame(iframe)

        # 제품 정보 이미지 다운로드
        product_images = driver.find_elements(By.CSS_SELECTOR, "#hdivDescription img")

        for idx, img in enumerate(product_images):
            time.sleep(random.uniform(2, 5))
            img_url = img.get_attribute("src")

            # 이미지 요청
            response = requests.get(img_url)
            response.raise_for_status()  # 요청이 실패하면 예외 발생

            # Pillow를 사용하여 이미지를 열고 저장
            image = Image.open(BytesIO(response.content))

            # 이미지 다운로드
            response = requests.get(img_url)
            if response.status_code == 200:
                file_extension = image.format.lower()  # 'jpeg', 'png' 등의 형식 반환
                file_path = os.path.join(images_dir, f"{productName.text}_product_image_{idx + 1}.{file_extension}")
                image.save(file_path)
                print(f"Downloaded {file_path}")

        # 원래 페이지로 돌아가기
        driver.switch_to.default_content()

        break
    elif re.match(r"^https://www\.11st", driver.current_url):
        print("11번가")
    elif re.match(r"^https://smartstore", driver.current_url):
        print("스마트스토어")
    elif re.match(r"^https://www\.lotteon", driver.current_url):
        print("롯데ON")
    elif re.match(r"^https://www\.coupang", driver.current_url):
        print("쿠팡")
    else:
        print("pass")

    print("")
    # 상세 페이지 작업 완료 후 탭 닫기
    driver.close()

    # 상품 가격 리스트 페이지 탭으로 돌아가서 닫기
    driver.switch_to.window(driver.window_handles[-1])
    driver.close()

    # 다시 리스트 페이지로 전환
    driver.switch_to.window(list_page_handle)
    print("Back to list page.")
    #현재 위치 출력
    print("크롬 드라이버 현재 URL: " + driver.current_url)
    print("크롬 드라이버 현재 URL Title: " + driver.title)




# for pageIdx in range(1):
#             time.sleep(2)

#             # 전체 상품 리스트 - div > basicList_basis__uNBZx
#             items = shopping.find_element(By.CLASS_NAME, "product_list")

#             crawledItems += adItems
            
#             # 미광고 제품 - div > product_inner__gr8QR
#             elements = items.find_elements(By.CLASS_NAME, "product_inner__gr8QR")
#             items = crawlItems(elements=elements, subDriver=subDriver, query=query)

#             crawledItems += items
#             count += len(items)
#             try: 
#                 shopping.find_element(By.CLASS_NAME, 'pagination_next__pZuC6').click()
#                 print("===========[{}] - [{}]".format(query, pageIdx))
#             except:
#                 print("===========[{}]가 마지막 페이지입니다.".format(pageIdx))
#                 break

#         print("===========[{}] 데이터 [{}] 건이 수집되었습니다.([{}]p)".format(query, adCount + count, pageCount))

#         search = shopping.find_element(By.XPATH, "/html/body/div/div/div[1]/div[2]/div/div[2]/div/div[2]/form/div[1]/div/input") # XPATH
#         search.send_keys(Keys.COMMAND, 'a')
#         search.send_keys(Keys.DELETE)
#         search.click()