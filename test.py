import os
import os.path
import re
import time
import csv
import uuid
import requests
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from PIL import Image
from io import BytesIO
from selenium.webdriver.common.action_chains import ActionChains
from multiprocessing import Pool

PROCESS_COUNT = 2
 
CRAWLING_DATA_CSV_FILE = 'CrawlingCategory.csv'
DATA_PATH = 'crawl_data'
IMAGES_PATH = "images"
THUMBS_PATH = "thumbnails"

DRIVER_PATH = 'chromedriver.exe'

DATA_DIVIDER = '---'
DATA_REMARK = '//'
DATA_ROW_DIVIDER = '_'
DATA_PRODUCT_DIVIDER = '|'

STR_NAME = 'name'
STR_URL = 'url'
CATEGORY3_SEQNO = 'category3Seqno'


class Crawler:


    def __init__(self):
        self.crawlingCategory = list()
        self.productSeqno = 1
        with open(CRAWLING_DATA_CSV_FILE, 'r', newline='', encoding='utf-8') as file:
            for crawlingValues in csv.reader(file, skipinitialspace=True):
                if not crawlingValues[0].startswith(DATA_REMARK):
                    self.crawlingCategory.append({STR_NAME: crawlingValues[1], STR_URL: crawlingValues[2], CATEGORY3_SEQNO: int(crawlingValues[0])})
    

    def StartCrawling(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--start-maximized") # 화면 최대화
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        self.options.add_argument("accept-language=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument('--disable-gpu')
        self.options.add_experimental_option("detach", True)

        # 멀티 프로세싱 대신 순차적으로 크롤링 실행
        for categoryValue in self.crawlingCategory:
            self.CrawlingCategory(categoryValue)
    
    
    def CrawlingCategory(self, categoryValue):
        crawlingName = categoryValue[STR_NAME]
        crawlingURL = categoryValue[STR_URL]
        category3Seqno = categoryValue[CATEGORY3_SEQNO]

        #data
        crawlingFile = open(f'{crawlingName}_crawledData.csv', 'w', newline='', encoding='utf8')
        crawlingData_csvWriter = csv.writer(crawlingFile)
        thumbnailFile = open(f'{crawlingName}_thumbnailFile.csv', 'w',newline='',encoding='utf-8')
        thumbnailFile_csvWriter = csv.writer(thumbnailFile)
        infoFile = open(f'{crawlingName}_infoFile.csv', 'w',newline='',encoding='utf-8')
        infoFile_csvWriter = csv.writer(infoFile)
    
        # 드라이버 생성
        service = webdriver.ChromeService(executable_path=DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=self.options)
        # 스텔스 모드
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win64",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        # 경로 설정
        if not os.path.exists(IMAGES_PATH):
            os.makedirs(IMAGES_PATH)
        if not os.path.exists(THUMBS_PATH):
            os.makedirs(THUMBS_PATH)
    
        # 카테고리 페이지로 이동
        driver.get(crawlingURL)
        driver.implicitly_wait(5)
        driver.find_element(By.XPATH, '//option[@value="90"]').click() #90개 보기
        wait = WebDriverWait(driver, 10)
        wait.until(EC.invisibility_of_element((By.CLASS_NAME, 'product_list_cover')))

        # 마우스 이벤트 시뮬레이션
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, "body"), 0, 0).perform()
        actions.move_by_offset(10, 20).perform()  # 무작위 위치로 이동
        time.sleep(random.uniform(2, 4))

        #subDriver = chrome_driver(DRIVER_PATH, headless=True)
        print("크롬 드라이버 현재 URL: " + driver.current_url)
        print("크롬 드라이버 현재 URL Title: " + driver.title)
        print("===========[{}] 데이터를 수집합니다.".format(crawlingName))

        # 리스트 페이지 핸들을 저장
        list_page_handle = driver.current_window_handle

        # 상품 리스트 불러오기
        itemList = driver.find_element(By.CLASS_NAME, "main_prodlist")
        all_items = itemList.find_elements(By.CLASS_NAME, "prod_item")
        items = [item for item in all_items if re.match(r"^productItem\d+", item.get_attribute("id"))]

        for item in items:

            print(f"prodcutSeqno: {self.productSeqno}")

            #상품 이름
            productName = item.find_element(By.CLASS_NAME, "prod_name").find_element(By.TAG_NAME, "a")
            productNameString = productName.text
            print(f"제품명: {productNameString}")
            
            #상품 가격
            priceText = item.find_element(By.CLASS_NAME, "price_sect").find_element(By.TAG_NAME, "a").text
            price = re.sub(r'\D', '', priceText)
            print(f"제품 가격: {price}")

            # 마우스 이동 시뮬레이션
            actions = ActionChains(driver)  # 액션 초기화
            actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, "body"), 0, 0).perform()
            actions.move_by_offset(10, 20).perform()
            time.sleep(random.uniform(2, 4))

            #상품 이름 클릭후 이동(상품 가격 리스트 페이지)
            print("상품 이름 클릭 전")
            productName.click()
            print("클릭 완료")
            time.sleep(random.uniform(3, 6))
            print("창 이동 전")
            driver.switch_to.window(driver.window_handles[-1])
            print("창 이동 완료")

            #쇼핑몰 필터링
            print("쇼핑몰 필터링 시작")
            a_element = driver.find_element(By.XPATH, "//tr[contains(@class, 'lowest')]/td[@class='mall']/div/a")
            img_elements = a_element.find_elements(By.TAG_NAME, "img")
            if img_elements:
                # img 태그가 있으면 alt 속성 값 가져오기
                mall_info = img_elements[0].get_attribute("alt")
                print(f"쇼핑몰 : {mall_info}")
            else:
                # img 태그가 없으면 title 속성 값 가져오기
                mall_info = a_element.get_attribute("title")
                print(f"쇼핑몰 : {mall_info}")
            if re.match(mall_info, "11번가"):
                pass
            elif re.match(mall_info, "G마켓"):
                pass
            elif re.match(mall_info, "쿠팡"):
                pass
            elif re.match(mall_info, "옥션"):
                pass
            else:
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(random.uniform(2, 4))
                driver.close()
                time.sleep(random.uniform(2, 4))
                driver.switch_to.window(list_page_handle)
                print("Back to list page.")
                continue

            #상품 정보
            print("상품 정보 찾기 전")
            productInfo = driver.find_element(By.XPATH, "//div[@class='items']").text
            print("상품 정보 찾기 완료")

            #최저가 사러가기 버튼 클릭 후 이동(상품 상세페이지)
            button = driver.find_element(By.CLASS_NAME, "buy_link")
            button.click()
            time.sleep(random.uniform(6, 10))
            driver.switch_to.window(driver.window_handles[-1])

            #현재 위치 출력
            print("크롬 드라이버 현재 URL: " + driver.current_url)
            print("크롬 드라이버 현재 URL Title: " + driver.title)

            # 스크롤 추가: 페이지 끝까지 무작위 간격으로 스크롤
            for _ in range(5):  # 5번 정도 스크롤을 시도
                scroll_position = random.randint(200, 800)  # 스크롤 길이 무작위 설정
                driver.execute_script(f"window.scrollBy(0, {scroll_position});")
                time.sleep(random.uniform(2, 4))  # 무작위 대기 시간 추가

            isSuccess = True
            #url 구분
            if re.match(r"^https://item\.gmarket", driver.current_url):
                print("G마켓")
                # 썸네일
                thumbnail_elements = driver.find_elements(By.CSS_SELECTOR, "ul.viewer img")
                isSuccess = self.thumbDownAucGma(thumbnail_elements, actions, productNameString, thumbnailFile_csvWriter, crawlingName, isSuccess)
                if not isSuccess:
                    print("썸네일 다운 실패")
                    pass
                # 상품 정보 이미지
                iframe = driver.find_element(By.ID, "detail1")
                isSuccess = self.imgDownAucGma(iframe, "gmarket", driver, actions, productNameString, infoFile_csvWriter, crawlingName, isSuccess)
                if not isSuccess:
                    print("이미지 다운 실패")
                    pass
            elif re.match(r"^http://itempage3\.auction", driver.current_url):
                print("Auction")
                # 썸네일
                thumbnail_elements = driver.find_elements(By.CSS_SELECTOR, "ul.viewer img")
                isSuccess = self.thumbDownAucGma(thumbnail_elements, actions, productNameString, thumbnailFile_csvWriter, crawlingName, isSuccess)
                if not isSuccess:
                    print("썸네일 다운 실패")
                    pass
                # 상품 정보 이미지
                iframe = driver.find_element(By.ID, "hIfrmExplainView")
                isSuccess = self.imgDownAucGma(iframe, "auction", driver, actions, productNameString, infoFile_csvWriter, crawlingName, isSuccess)
                if not isSuccess:
                    print("이미지 다운 실패")
                    pass
            elif re.match(r"^https://www\.11st", driver.current_url):
                print("11번가")
                # 썸네일
                thumbnail_elements = driver.find_elements(By.XPATH, "//div[@id='productImg']/div/img")
                isSuccess = self.thumbDownAucGma(thumbnail_elements, actions, productNameString, thumbnailFile_csvWriter, crawlingName, isSuccess)
                if not isSuccess:
                    print("썸네일 다운 실패")
                    pass
                # 상품 정보 이미지
                try:
                    # iframe 존재 여부 확인
                    iframe = driver.find_element(By.ID, "prdDescIfrm")
                    print("iframe이 발견되었습니다. iframe 내부 이미지를 처리합니다.")
                    isSuccess = self.imgDownAucGma(iframe, "11st", driver, actions, productNameString, infoFile_csvWriter, crawlingName, isSuccess)
                    if not isSuccess:
                        print("이미지 다운 실패")
                        pass
                except Exception as e:
                    # iframe이 없는 경우 처리
                    print("iframe이 발견되지 않았습니다. iframe 외부 이미지를 처리합니다.")
                    prod_images = driver.find_elements(By.XPATH, "//div[@class='prdc_bo_detail']//img")
                    isSuccess = self.imgDownCoupang(prod_images, driver, actions, productNameString, infoFile_csvWriter, crawlingName, isSuccess)
                    if not isSuccess:
                        print("이미지 다운 실패")
                        pass
            elif re.match(r"^https://www\.lotteon", driver.current_url):
                print("롯데ON")
                continue
            elif re.match(r"^https://www\.coupang", driver.current_url):
                print("쿠팡")
                # 썸네일
                thumbnail_image = driver.find_element(By.CLASS_NAME, "prod-image__detail")
                thumbnail_elements = driver.find_elements(By.CLASS_NAME, "prod-image__item")
                isSuccess = self.thumbDownCoupang(thumbnail_image, thumbnail_elements, actions, productNameString, thumbnailFile_csvWriter, crawlingName, isSuccess)
                if not isSuccess:
                    print("썸네일 다운 실패")
                    pass
                # 상품 정보 이미지
                prod_images = driver.find_elements(By.XPATH, "//div[@class='product-detail-content-inside']//img")
                isSuccess = self.imgDownCoupang(prod_images, driver, actions, productNameString, infoFile_csvWriter, crawlingName, isSuccess)
                if not isSuccess:
                    print("이미지 다운 실패")
                    pass
            else:
                print("pass")
                isSuccess = False
                pass

            # 스크롤 추가
            for _ in range(5):
                scroll_position = random.randint(200, 800)
                driver.execute_script(f"window.scrollBy(0, {scroll_position});")
                time.sleep(random.uniform(2, 4))

            # 원래 페이지로 돌아가기
            driver.switch_to.default_content()

            # 상세 페이지 작업 완료 후 탭 닫기
            time.sleep(random.uniform(2, 5))
            driver.close()

            # 상품 가격 리스트 페이지 탭으로 돌아가서 닫기
            time.sleep(random.uniform(2, 4))
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(random.uniform(2, 4))
            driver.close()

            # 다시 리스트 페이지로 전환
            time.sleep(random.uniform(2, 4))
            driver.switch_to.window(list_page_handle)
            print("Back to list page.")
            #현재 위치 출력
            print("크롬 드라이버 현재 URL: " + driver.current_url)
            print("크롬 드라이버 현재 URL Title: " + driver.title)

            if isSuccess:
                crawlingData_csvWriter.writerow([self.productSeqno, category3Seqno, productNameString, price, productInfo])
                self.productSeqno += 1

        crawlingFile.close()
        print("Crawling Finish: " + crawlingName)
    
    # 썸네일
    def thumbDownAucGma(self, thumbnail_elements, actions, productNameString, thumbnailFile_csvWriter, crawlingName, isSuccess):

        # 카테고리별 폴더 생성
        category_folder = os.path.join(THUMBS_PATH, crawlingName)
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)  # 카테고리 폴더가 없으면 생성
        
        for idx, img in enumerate(thumbnail_elements):
            time.sleep(random.uniform(2, 4))

            img_url = img.get_attribute("src")
            if img_url.startswith("//"):  # URL이 //로 시작하면 http 추가
                img_url = "https:" + img_url

            # 이미지 요청
            try:
                response = requests.get(img_url, timeout=4)
                response.raise_for_status()  # 상태 코드 확인
                image = Image.open(BytesIO(response.content))
                if response.status_code == 200:
                    file_extension = image.format.lower()  # 'jpeg', 'png' 등의 형식 반환
                    orgProductThumbFileName = productNameString + "_productImage_" + str(idx) + file_extension
                    storedPrdocutThumbFileName = uuid.uuid4().hex+ file_extension
                    file_path = os.path.join(category_folder, f"{storedPrdocutThumbFileName}.{file_extension}")
                    image.save(file_path)
                    print(f"썸네일 다운로드 완료: {file_path}")
                # csv에 저장
                isThumb = "N"
                if idx == 0:
                    isThumb = "Y"
                thumbnailFile_csvWriter.writerow([self.productSeqno, orgProductThumbFileName, storedPrdocutThumbFileName, isThumb])
                isSuccess = True
            except requests.exceptions.HTTPError as e:
                isSuccess = False
                print(f"HTTP 에러 발생: {e}, URL: {img_url}")
                return isSuccess
            except requests.exceptions.RequestException as e:
                isSuccess = False
                print(f"요청 실패: {e}, URL: {img_url}")
                return isSuccess
        return isSuccess

    
    # 쿠팡 썸네일
    def thumbDownCoupang(self, thumbnail_img, thumbnail_elements, actions, productNameString, thumbnailFile_csvWriter, crawlingName, isSuccess):

        # 카테고리별 폴더 생성
        category_folder = os.path.join(THUMBS_PATH, crawlingName)
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)  # 카테고리 폴더가 없으면 생성

        for idx, img in enumerate(thumbnail_elements):
            # 썸네일 마우스 이동
            actions.move_to_element(img)
            time.sleep(random.uniform(2, 4))

            img_url = thumbnail_img.get_attribute("src")
            if img_url.startswith("//"):  # URL이 //로 시작하면 http 추가
                img_url = "https:" + img_url

            # 이미지 요청
            try:
                response = requests.get(img_url, timeout=4)
                response.raise_for_status()  # 상태 코드 확인
                image = Image.open(BytesIO(response.content))
                if response.status_code == 200:
                    file_extension = image.format.lower()  # 'jpeg', 'png' 등의 형식 반환
                    orgProductThumbFileName = productNameString + "_productImage_" + str(idx) + file_extension
                    storedPrdocutThumbFileName = uuid.uuid4().hex+ file_extension
                    file_path = os.path.join(category_folder, f"{storedPrdocutThumbFileName}.{file_extension}")
                    image.save(file_path)
                    print(f"썸네일 다운로드 완료: {file_path}")
                # csv에 저장
                isThumb = "N"
                if idx == 0:
                    isThumb = "Y"
                thumbnailFile_csvWriter.writerow([self.productSeqno, orgProductThumbFileName, storedPrdocutThumbFileName, isThumb])
                isSuccess = True
            except requests.exceptions.HTTPError as e:
                isSuccess = False
                print(f"HTTP 에러 발생: {e}, URL: {img_url}")
                return isSuccess
            except requests.exceptions.RequestException as e:
                isSuccess = False
                print(f"요청 실패: {e}, URL: {img_url}")
                return isSuccess
        return isSuccess
                

    #제품 정보 사진
    def imgDownAucGma(self, iframe, shop, driver, actions, productNameString, infoFile_csvWriter, crawlingName, isSuccess):

        # 카테고리별 폴더 생성
        category_folder = os.path.join(IMAGES_PATH, crawlingName)
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)  # 카테고리 폴더가 없으면 생성

        # 스크롤 추가: 페이지 끝까지 무작위 간격으로 스크롤
        for _ in range(5):  # 5번 정도 스크롤을 시도
            scroll_position = random.randint(200, 800)  # 스크롤 길이 무작위 설정
            driver.execute_script(f"window.scrollBy(0, {scroll_position});")
            time.sleep(random.uniform(2, 4))  # 무작위 대기 시간 추가

        #iframe으로 이동
        driver.switch_to.frame(iframe)
        print("iFrame 전환 완료. HTML 확인:")
        print(driver.page_source[:1000])

        # 제품 정보 이미지 다운로드
        # 이미지 리스트
        print("상세이미지 선택")
        product_images = driver.find_elements(By.XPATH, "//img")
        print(f"찾은 이미지 개수: {len(product_images)}")

        for idx, img in enumerate(product_images):
            print("상세 이미지 다운 시작")

            # 스크롤 이동: 요소가 화면에 나타나도록
            driver.execute_script("arguments[0].scrollIntoView();", img)
            time.sleep(0.5)  # 스크롤 후 잠시 대기

            time.sleep(random.uniform(1, 2))

            img_url = img.get_attribute("src")

            # 이미지 요청
            try:
                response = requests.get(img_url, timeout=4)
                response.raise_for_status()  # 상태 코드 확인
                image = Image.open(BytesIO(response.content))
                if response.status_code == 200:
                    file_extension = image.format.lower()  # 'jpeg', 'png' 등의 형식 반환
                    orgProductImageFileName = productNameString + "_productImage_" + str(idx) + file_extension
                    storedPrdocutImageFileName = uuid.uuid4().hex+ file_extension
                    file_path = os.path.join(category_folder, f"{storedPrdocutImageFileName}.{file_extension}")
                    image.save(file_path)
                    print(f"이미지 다운로드 완료: {file_path}")
                # csv에 저장
                infoFile_csvWriter.writerow([self.productSeqno, orgProductImageFileName, storedPrdocutImageFileName])
                isSuccess = True
            except requests.exceptions.HTTPError as e:
                isSuccess = False
                print(f"HTTP 에러 발생: {e}, URL: {img_url}")
                return isSuccess
            except requests.exceptions.RequestException as e:
                isSuccess = False
                print(f"요청 실패: {e}, URL: {img_url}")
                return isSuccess
        
        driver.switch_to.default_content()
        return isSuccess

        
    # 쿠팡 제품 정보 이미지
    def imgDownCoupang(self, imgs, driver, actions, productNameString, infoFile_csvWriter, crawlingName, isSuccess):

        # 카테고리별 폴더 생성
        category_folder = os.path.join(IMAGES_PATH, crawlingName)
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)  # 카테고리 폴더가 없으면 생성

        for idx, img in enumerate(imgs):
            # 스크롤 추가: 페이지 끝까지 무작위 간격으로 스크롤
            for _ in range(5):  # 5번 정도 스크롤을 시도
                scroll_position = random.randint(200, 800)  # 스크롤 길이 무작위 설정
                driver.execute_script(f"window.scrollBy(0, {scroll_position});")
                time.sleep(random.uniform(2, 4))  # 무작위 대기 시간 추가
            # 마우스 이동 시뮬레이션
            time.sleep(random.uniform(2, 4))

            img_url = img.get_attribute("src")

            # 이미지 요청
            try:
                response = requests.get(img_url, timeout=4)
                response.raise_for_status()  # 상태 코드 확인
                image = Image.open(BytesIO(response.content))
                if response.status_code == 200:
                    file_extension = image.format.lower()  # 'jpeg', 'png' 등의 형식 반환
                    orgProductImageFileName = productNameString + "_productImage_" + str(idx) + file_extension
                    storedPrdocutImageFileName = uuid.uuid4().hex+ file_extension
                    file_path = os.path.join(category_folder, f"{storedPrdocutImageFileName}.{file_extension}")
                    image.save(file_path)
                    print(f"이미지 다운로드 완료: {file_path}")
                # csv에 저장
                infoFile_csvWriter.writerow([self.productSeqno, orgProductImageFileName, storedPrdocutImageFileName])
                isSuccess = True
            except requests.exceptions.HTTPError as e:
                isSuccess = False
                print(f"HTTP 에러 발생: {e}, URL: {img_url}")
                return isSuccess
            except requests.exceptions.RequestException as e:
                isSuccess = False
                print(f"요청 실패: {e}, URL: {img_url}")
                return isSuccess
        return isSuccess


    def CreateCSV(self):
        if not os.path.exists(DATA_PATH):
            os.mkdir(DATA_PATH)

if __name__ == '__main__':
    crawler = Crawler()
    crawler.CreateCSV()
    crawler.StartCrawling()