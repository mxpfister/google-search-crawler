from src.database import Database
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
import time
import configparser

config = configparser.ConfigParser()
config.read("../config.properties")


class GoogleCrawler:
    def __init__(self):
        self.cookie_consent_button_id = "L2AGLb"
        self.insert_statement = "insert into google_results (heading, url, search_term, date_time) values (" \
                                "%s, %s, %s, %s)"
        self.db = self.initialize_database()
        self.driver = self.initialize_webdriver()

    def initialize_webdriver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        return webdriver.Chrome(options=chrome_options)

    def initialize_database(self):
        db = Database(config["database"]["host"],
                      config["database"]["username"],
                      config["database"]["password"],
                      config["database"]["database"])
        db.initialize_table()
        return db

    def do_cookie_consent(self):
        time.sleep(2)
        ActionChains(self.driver).click(self.driver.find_element(by=By.ID, value=self.cookie_consent_button_id)).perform()
        time.sleep(5)

    def prepare_searchterm(self, searchterm):
        return searchterm.replace(" ", "+")

    def extract_data(self, max_results=100):
        wait = WebDriverWait(self.driver, 5)
        links_with_text = []
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while len(links_with_text) < max_results:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                try:
                    load_more_button = wait.until(
                        ec.element_to_be_clickable((By.XPATH, "//div[5]/div/div[12]/div[1]/div[4]/div/div[4]/div["
                                                              "4]/a[1]")))
                    load_more_button.click()
                    time.sleep(2)
                except:
                    print("Button not found.")
                    break
            last_height = new_height

            search_results = self.driver.find_elements(By.XPATH, "//a[@href]//h3")
            for result in search_results:
                link = result.find_element(By.XPATH, "./ancestor::a").get_attribute("href")
                link_text = result.text
                if {"text": link_text, "url": link} not in links_with_text and len(links_with_text) < max_results:
                    links_with_text.append({"heading": link_text, "url": link, "date_time": self.get_now()})
        return links_with_text

    def crawl_google(self, searchterm, max_results=100):
        url = "https://www.google.com/search?q=" + self.prepare_searchterm(searchterm)
        self.driver.get(url)

        try:
            self.do_cookie_consent()
        except NoSuchElementException:
            pass
        finally:
            results = self.extract_data(max_results)
            if len(results) > 0:
                self.safe_results(results, searchterm)

    def safe_results(self, results, searchterm):
        print(results)
        for result in results:
            self.db.execute_query(self.insert_statement, (result["heading"], result["url"], searchterm, result["date_time"]))

    def get_now(self):
        return time.strftime('%Y-%m-%d %H:%M:%S')

    def close(self):
        self.driver.quit()
        self.db.connection.close()
