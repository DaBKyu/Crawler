from openpyxl import *
from selenium import webdriver
from selenium.webdriver.common.by import By

def chrome_driver(chromeDriverPath, headless = False):
    service = webdriver.ChromeService(executable_path=chromeDriverPath, log_output='log/test_log')
    options = webdriver.ChromeOptions() # 옵션 지정 객체
    options.add_argument("--start-maximized") # 화면 최대화
    if headless:
        options.add_argument("--headless") # 백그라운드 명시적 지정
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def setupBeforeCrawling(driver):
    # 다나와 메인 페이지 이동
    driver.get("https://www.danawa.com/")

    # 로딩 대기
    driver.implicitly_wait(5)

    # 검색창 클릭
    driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/div/div[5]/ul/li[4]/a").click() # XPATH
    driver.implicitly_wait(3)

    return driver