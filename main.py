from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import threading
import concurrent.futures


def get_next_page_url(driver):
    try:
        next_page_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//a[@data-testid="pagination-forward"]')))
        return next_page_button.get_attribute('href')
    except Exception as e:
        return None

def clear_browser_data(driver):
    driver.delete_all_cookies()

    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")

def parse_apartment(driver, apartment_url):
    try:
        driver.get(apartment_url)

        price = driver.find_element(By.XPATH, '//h3[@class="css-12vqlj3"]').text
        box_elements = [element.text for element in driver.find_elements(By.XPATH, '//p[@class="css-b5m1rv er34gjf0"]')]
    
        for element in box_elements:
            if 'Поверх: ' in element:
                floor = element.split(' ')[1]
            elif 'Поверховість: ' in element:
                floors_count = element.split(' ')[1]
            elif 'Загальна площа: ' in element:
                area = element.split(' ')[2]
    
        location = driver.find_element(By.XPATH, '//img[@class="css-149mw5z"]').get_attribute("alt")
        
        clear_browser_data(driver)
        return [price, floor, floors_count, location, area]
    except Exception as e:

        clear_browser_data(driver)
        return None

def main():
    options = Options()
    driver = webdriver.Chrome(options=options)

    driver.implicitly_wait(5)


    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name('CloudDemo_JJ.json', scope)
    client = gspread.authorize(credentials)


    spreadsheet = client.open('OLX apartments')
    sheet = spreadsheet.worksheet('parsed data')

    url = 'https://www.olx.ua/uk/nedvizhimost/kvartiry/dolgosrochnaya-arenda-kvartir/?currency=UAH'
    
    driver.get(url)

    data = []

    ALL_LINKS = []

    while True:
        time.sleep(1)

        [ ALL_LINKS.append(element.get_attribute("href")) for element in driver.find_elements(By.XPATH, '//a[@class="css-z3gu2d"]')[::2]]

        
        next_page_url = get_next_page_url(driver)
        if next_page_url is None:
            break
        else:
            driver.get(next_page_url)

    for n, apartment_url in enumerate(ALL_LINKS):
      if n % 40 == 0 and n > 0:
        driver.quit()
        del driver
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)
        driver.get(apartment_url)
        data.append(parse_apartment(driver, apartment_url))
      else:
        data.append(parse_apartment(driver, apartment_url))
      
    data = [line for line in data if line is not None]

    driver.quit()

    df = pd.DataFrame(data, columns=['Price', 'Floor', 'Floors_count', 'Location', 'Area'])
    sheet.update([df.columns.tolist()] + df.values.tolist())

main()
