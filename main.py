import time, sys

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from openpyxl import Workbook, load_workbook

from utils import *

driver_path = 'C:\\Users\\gladius\\Desktop\\Crawl\\chromedriver-win64\\chromedriver.exe'
delivery_name = datetime.now().strftime("%Y%m%d_%H%M%s")

if __name__ == "__main__":
    if sys.argv[-1] == sys.argv[0]:
        print("쿼리 시트가 입력되지 않았습니다.")
        print("사용 방법은 main.py [쿼리 시트 명]입니다. 다시 시도해주세요")
        exit(1)
    elif len(sys.argv) >= 3:
        print("쿼리 시트 지정이 정확하지 않습니다.")
        print("입력된 매개 변수의 수가", len(sys.argv) - 1, "개입니다.")
        print("사용 방법은 main.py [쿼리 시트 명]입니다. 다시 시도해주세요")
        exit(1)
    else:
        fileName = sys.argv[1]
        queryPath = "queries/" + fileName + '.xlsx'
        try:
            print(fileName, "쿼리 시트에서 쿼리를 읽습니다.")
            querieXlsx = load_workbook(queryPath, data_only=True)
            queriesSheet = querieXlsx['시트1']
            queries = []
            for index, row in enumerate(queriesSheet.rows):
                if index == 0:
                    continue
                queries.append(row[0].value)
            print(len(queries), "개의 쿼리가 정상적으로 확인되었습니다.")
        except:
            print(fileName, "쿼리 시트에서 쿼리를 읽을 수 없습니다.")
            print("파일 이름 또는 시트 구조를 확인해주세요")
            exit(1)

    start_time = time.time()
    driver = chrome_driver(driver_path)
    shopping = setupBeforeCrawling(driver)

    # 검색어 입력창 선택
    search = shopping.find_element(By.XPATH, "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div[1]/form/fieldset/div[1]/input[1]")
    search.click()

    crawledItems = []
    for query in queries:
        # 쿼리 검색
        search.send_keys(query)
        search.send_keys(Keys.ENTER)
        shopping.implicitly_wait(3)
        count = 0