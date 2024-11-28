from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime
from datetime import timedelta
import csv
import os
import os.path
import shutil
import traceback

from multiprocessing import Pool

PROCESS_COUNT = 2

CRAWLING_DATA_CSV_FILE = 'CrawlingCategory.csv'
DATA_PATH = 'crawl_data'
DATA_REFRESH_PATH = f'{DATA_PATH}/Last_Data'

TIMEZONE = 'Asia/Seoul'

CHROMEDRIVER_PATH = 'chromedriver.exe'

DATA_DIVIDER = '---'
DATA_REMARK = '//'
DATA_ROW_DIVIDER = '_'
DATA_PRODUCT_DIVIDER = '|'

STR_NAME = 'name'
STR_URL = 'url'
STR_CRAWLING_PAGE_SIZE = 'crawlingPageSize'


class DanawaCrawler:
    def __init__(self):
        self.crawlingCategory = list()
        with open(CRAWLING_DATA_CSV_FILE, 'r', newline='') as file:
            for crawlingValues in csv.reader(file, skipinitialspace=True):
                if not crawlingValues[0].startswith(DATA_REMARK):
                    self.crawlingCategory.append({STR_NAME: crawlingValues[0], STR_URL: crawlingValues[1], STR_CRAWLING_PAGE_SIZE: int(crawlingValues[2])})

    def StartCrawling(self):
        self.chrome_option = webdriver.ChromeOptions()
        self.chrome_option.add_argument('--headless')
        self.chrome_option.add_argument('--window-size=1920,1080')
        self.chrome_option.add_argument('--start-maximized')
        self.chrome_option.add_argument('--disable-gpu')
        self.chrome_option.add_argument('lang=ko=KR')

        if __name__ == '__main__':
            pool = Pool(processes=PROCESS_COUNT)
            pool.map(self.CrawlingCategory, self.crawlingCategory)
            pool.close()
            pool.join()
            
    
    def CrawlingCategory(self, categoryValue):
        crawlingName = categoryValue[STR_NAME]
        crawlingURL = categoryValue[STR_URL]
        crawlingSize = categoryValue[STR_CRAWLING_PAGE_SIZE]

        print('Crawling Start : ' + crawlingName)

        # data
        crawlingFile = open(f'{crawlingName}.csv', 'w', newline='', encoding='utf8')
        crawlingData_csvWriter = csv.writer(crawlingFile)
        crawlingData_csvWriter.writerow([self.GetCurrentDate().strftime('%Y-%m-%d %H:%M:%S')])
        
        try:
            browser = webdriver.Chrome(CHROMEDRIVER_PATH, options=self.chrome_option)
            browser.implicitly_wait(5)
            browser.get(crawlingURL)

            browser.find_element_by_xpath('//option[@value="90"]').click()
        
            wait = WebDriverWait(browser, 10)
            wait.until(EC.invisibility_of_element((By.CLASS_NAME, 'product_list_cover')))
            
            for i in range(-1, crawlingSize):
                if i == -1:
                    browser.find_element_by_xpath('//li[@data-sort-method="NEW"]').click()
                elif i == 0:
                    browser.find_element_by_xpath('//li[@data-sort-method="BEST"]').click()
                elif i > 0:
                    if i % 10 == 0:
                        browser.find_element_by_xpath('//a[@class="edge_nav nav_next"]').click()
                    else:
                        browser.find_element_by_xpath('//a[@class="num "][%d]'%(i%10)).click()
                wait.until(EC.invisibility_of_element((By.CLASS_NAME, 'product_list_cover')))
                
                # Get Product List
                productListDiv = browser.find_element_by_xpath('//div[@class="main_prodlist main_prodlist_list"]')
                products = productListDiv.find_elements_by_xpath('//ul[@class="product_list"]/li')

                for product in products:
                    if not product.get_attribute('id'):
                        continue

                    # ad
                    if 'prod_ad_item' in product.get_attribute('class').split(' '):
                        continue
                    if product.get_attribute('id').strip().startswith('ad'):
                        continue

                    productId = product.get_attribute('id')[11:]
                    productName = product.find_element_by_xpath('./div/div[2]/p/a').text.strip()
                    productPrices = product.find_elements_by_xpath('./div/div[3]/ul/li')
                    productPriceStr = ''

                    # Check Mall
                    isMall = False
                    if 'prod_top5' in product.find_element_by_xpath('./div/div[3]').get_attribute('class').split(' '):
                        isMall = True
                    
                    if isMall:
                        for productPrice in productPrices:
                            if 'top5_button' in productPrice.get_attribute('class').split(' '):
                                continue
                            
                            if productPriceStr:
                                productPriceStr += DATA_PRODUCT_DIVIDER
                            
                            mallName = productPrice.find_element_by_xpath('./a/div[1]').text.strip()
                            if not mallName:
                                mallName = productPrice.find_element_by_xpath('./a/div[1]/span[1]').text.strip()
                            
                            price = productPrice.find_element_by_xpath('./a/div[2]/em').text.strip()

                            productPriceStr += f'{mallName}{DATA_ROW_DIVIDER}{price}'
                    else:
                        for productPrice in productPrices:
                            if productPriceStr:
                                productPriceStr += DATA_PRODUCT_DIVIDER
                            
                            # Default
                            productType = productPrice.find_element_by_xpath('./div/p').text.strip()

                            # like Ram/HDD/SSD
                            # HDD : 'WD60EZAZ, 6TB\n25원/1GB_149,000'
                            productType = productType.replace('\n', DATA_ROW_DIVIDER)

                            # Remove rank text
                            # 1위, 2위 ...
                            productType = self.RemoveRankText(productType)
                            
                            price = productPrice.find_element_by_xpath('./p[2]/a/strong').text.strip()

                            if productType:
                                productPriceStr += f'{productType}{DATA_ROW_DIVIDER}{price}'
                            else:
                                productPriceStr += f'{price}'
                    
                    crawlingData_csvWriter.writerow([productId, productName, productPriceStr])

        except Exception as e:
            print('Error - ' + crawlingName + ' ->')
            print(traceback.format_exc())
            self.errorList.append(crawlingName)

        crawlingFile.close()

        print('Crawling Finish : ' + crawlingName)

    def RemoveRankText(self, productText):
        if len(productText) < 2:
            return productText
        
        char1 = productText[0]
        char2 = productText[1]

        if char1.isdigit() and (1 <= int(char1) and int(char1) <= 9):
            if char2 == '위':
                return productText[2:].strip()
        
        return productText

    def DataRefresh(self):

        if not os.path.exists(DATA_PATH):
            os.mkdir(DATA_PATH)


if __name__ == '__main__':
    crawler = DanawaCrawler()
    crawler.DataRefresh()
    crawler.StartCrawling()