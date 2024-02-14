# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from datetime import datetime
from scrapy.item import Item, Field


class PriceComparatorItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class TunisianetItem(Item):
   

    name = Field()
    link = Field()
    Url = Field()
    category = Field()
    productname = Field()
    reference = Field()
    price = Field()
    availability = Field()
    brand = Field()
    imageUrl = Field()
    
    
class MytekItem(Item):
   

    name = Field()
    link = Field()
    Url = Field()
    category = Field()
    productname = Field()
    reference = Field()
    price = Field()
    availability = Field()
    brand = Field()
    imageUrl = Field()
    
    
    
    
        