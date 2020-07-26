# -*- coding: utf-8 -*-
import os
import time
import random
import json
import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.support.expected_conditions as ec
import traceback
from scrapy.http import Request
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait

from . import cities

base_dir = os.path.dirname(os.path.abspath(__file__))

class YelpSearchSpider(scrapy.Spider):
    name = 'yelp-search'
    allowed_domains = ['yelp.com']

    def __init__(self, *args, **kwargs):
        self.result = dict()
        self.proxy_list = [
            "http://68621db5fccd4d04aabac3f424b0673b:@proxy.crawlera.com:8010/",
            "http://84dd43ea0c64481981ef0bf55bebf2c7:@proxy.crawlera.com:8010/",
        ]
        self.search_url = "https://www.yelp.com/search?find_desc=Restaurants&find_loc={location}&ns=1"
        self.cities = cities.cities_list

    def get_random_proxy(self):
        random_idx = random.randint(0, len(self.proxy_list)-1)
        proxy_ip = self.proxy_list[random_idx]
        return proxy_ip

    def set_driver(self):
        random_proxy_ip = self.get_random_proxy()        
        webdriver.DesiredCapabilities.CHROME['proxy'] = {
            "httpProxy":random_proxy_ip,
            "ftpProxy":random_proxy_ip,
            "sslProxy":random_proxy_ip,
            "proxyType":"MANUAL",
        }    
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.132 Safari/537.36'
        chrome_option = webdriver.ChromeOptions()
        chrome_option.add_argument('--no-sandbox')
        chrome_option.add_argument('--disable-dev-shm-usage')
        chrome_option.add_argument('--ignore-certificate-errors')
        chrome_option.add_argument("--disable-blink-features=AutomationControlled")
        chrome_option.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.132 Safari/537.36')
        chrome_option.headless = True
        
        driver = webdriver.Chrome(options = chrome_option)
        return driver

    def start_requests(self):
        yield Request("https://www.google.com/", callback=self.parse_search)

    def parse_search(self, response):
        for city in self.cities:
            
            # /* Get Restaurant URLs */
            try:
                lst = []
                
                self.driver = self.set_driver()
                self.driver.get(self.search_url.format(location = city))

                i=0
                while True:
                    # get restaurants urls
                    rest_items = self.driver.find_element_by_xpath('//*[@id="wrap"]/div[3]/div[2]/div/div[1]/div[1]/div[2]/div[2]/ul/li/div/div/div/div[2]/div[1]/div/div[1]/div/div[1]/div/div/h4/span/a')

                    for rest_item in rest_items:
                        rest_url = rest_item.get_attribute('href').strip()
                        if rest_url:
                            lst.append(rest_url)
                    
                    try:
                        next_page_btn = self.driver.find_element_by_xpath('//*[@id="wrap"]/div[3]/div[2]/div/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/div/div[last()]/span/a')

                        if next_page_btn:
                            i += 1
                            next_page_btn.click()
                            print('-----------------')
                            print("Clicked Next Page Button", i, "times")
                        else:
                            break
                    except:
                        break

                self.driver.quit()
            except:
                # print(traceback.print_exc())
                print("element not found..")
                self.driver.quit()
            
            print('---------------------------------------------------------')
            print(lst)
            time.sleep(20)

            # /* Get Restaurant Attributes */
            for rest_url in lst:
                    
                try:
                    self.driver = self.set_driver()
                    self.driver.get(rest_url)
                    time.sleep(10)
                    page_source = self.driver.page_source
                    time.sleep(10)
                    result_dict = {
                        "CITY" : city,
                        "RESTNAME" : "",
                        "ADDRESS" : "",
                        # "TIME" : "",
                        "RATINGS" : "",
                        "MENU" : [],
                    }

                    soup = BeautifulSoup(page_source, 'lxml')
                    if soup:
                        rest_name = soup.xpath('//*[@id="wrap"]/div[4]/div/div[4]/div/div/div[2]/div/div/div[1]/div/div[1]/div[1]/div/div/div[1]/h1')
                        if rest_name:
                            result_dict["RESTNAME"] = rest_name.text.strip()

                        location = soup.xpath('//*[@id="wrap"]/div[4]/div/div[4]/div/div/div[2]/div/div/div[1]/div/div[1]/div[1]/div/div/span[last()]')
                        if location:
                            result_dict["ADDRESS"] = location.text.strip()

                        # phone_num = soup.xpath('div.restaurantSummary-info span[data-testid="restaurant-phone"]')
                        # if phone_num:
                        #     result_dict["PHONE"] = phone_num.text.strip()

                        # open_time = soup.xpath('div.sc-dcOKER span.hlXfBB')
                        # if open_time:
                        #     result_dict["TIME"] = open_time.text.strip()
                        
                            
                        temp_dict = dict()
                        
                        ratings = soup.xpath('//*[@id="wrap"]/div[4]/div/div[4]/div/div/div[2]/div/div/div[1]/div/div[1]/div[1]/div/div/div[2]/div[1]/span/div/img')
                        print(ratings)

                        rating_text = soup.xpath('//*[@id="wrap"]/div[4]/div/div[4]/div/div/div[2]/div/div/div[1]/div/div[1]/div[1]/div/div/div[2]/div[2]/p')
                        if rating_text:
                            temp_dict["VOLUME"] = rating_text.text.strip()
                        
                        popular_sec = soup.select_one('div#menuSectionpopularItems')
                        popular_items = list()
                        for popular_item in popular_sec.select('ghs-restaurant-menu-item'):
                            popular_item_dict = dict()
                            pop_menu_name = popular_item.select_one('a[itemprop="name"]')
                            if pop_menu_name:
                                popular_item_dict["POP_NAME"] = pop_menu_name.text.strip()
                            
                            pop_menu_desc = popular_item.select_one('p[itemprop="description"]')
                            if pop_menu_desc:
                                popular_item_dict["POP_DESCRIPTION"] = pop_menu_desc.text.strip()

                            pop_menu_price = popular_item.select_one('span[itemprop="price"]')
                            if pop_menu_price:
                                popular_item_dict["POP_PRICE"] = pop_menu_price.text.strip()

                            popular_items.append(popular_item_dict)
                            temp_dict["POPULAR_ITEMS"] = popular_items
                            result_dict['RATINGS'] = temp_dict

                        
                        menu_items = soup.select('ghs-restaurant-menu-section ghs-restaurant-menu-item')
                        for menu_item in menu_items:
                            menu_dict = dict()
                            menu_name = menu_item.select_one('a[itemprop="name"]')
                            if menu_name:
                                menu_dict["NAME"] = menu_name.text.strip()
                            
                            menu_desc = menu_item.select_one('p[itemprop="description"]')
                            if menu_desc:
                                menu_dict["DESCRIPTION"] = menu_desc.text.strip()

                            menu_price = menu_item.select_one('span[itemprop="price"]')
                            if menu_price:
                                menu_dict["PRICE"] = menu_price.text.strip()

                            menu_img = menu_item.select_one('img')
                            if menu_img:
                                menu_dict["IMAGE"] = menu_img["src"].strip()

                            result_dict["MENU"].append(menu_dict)
                
                    if result_dict["RESTNAME"]:
                        yield result_dict     
                    
                    self.driver.quit()
                except Exception as e:
                    print(e)
                    self.driver.quit()
                    continue
            
            return