# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RestaurantItem(scrapy.Item):
    name = scrapy.Field()
    yelp_url = scrapy.Field()
    categories = scrapy.Field()
    address = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()
    zipcode = scrapy.Field()
    website = scrapy.Field()
    phone = scrapy.Field()
    popular_items = scrapy.Field()
    hours = scrapy.Field()
    images = scrapy.Field()
