import random
import time
import scrapy
from datetime import datetime
from price_comparator.items import MytekItem


class TunisianetSpider(scrapy.Spider):
    now = datetime.now()
    Nowdate = now.strftime("%Y-%m-%d %H:%M:%S")

    current_time = now.strftime("%Y_%m_%d_%H_%M_%S")

    name = 'Mytek'
    custom_settings = {
        'FEEDS': {
            "dataproduct/MytekProduct"+current_time+".json": {
                "format": "json",
                "overwrite": True,
            }
        },
        'ROBOTSTXT_OBEY': False,
        "COOKIES_ENABLED": True,
        "COOKIES_DEBUG": True,
        "ITEM_PIPELINES": {
            'price_comparator.pipelines.MytekPipline': 300,
        }


    }

    start_urls = [
        'https://www.mytek.tn/catalogsearch/result/index/?product_list_order=price&q=[', ]

    def start_requests(self):

        user_agent_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15']
        user_agent = random.choice(user_agent_list)
        print ("user agent : " , user_agent)
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        for url in self.start_urls:

            yield scrapy.Request(url=url, callback=self.parse, headers=headers)

    def parse(self, response):
        products = response.css('li.item.product.product-item')
        print(len(products))
        item = MytekItem()
        for product in products:
            try:
                url = product.css(
                    'a.product-item-link::attr(href)').extract_first()
                item['Url'] = url
            except AttributeError:
                item['Url'] = ''
            try:
                price_selector = product.css(
                    'span[data-price-type="finalPrice"]::attr(data-price-amount)')
                if price_selector:
                    price = float(price_selector.extract_first())
                    item['price'] = price
                else:
                    item['price'] = None
            except (AttributeError, ValueError):
                # Set default value for price when an error occurs
                item['price'] = None

            # Set default value for category when an error occurs
            item['category'] = ''

            try:
                item['productname'] = product.css(
                    'a.product-item-link::text').get()
            except AttributeError:
                # Set default value for productname when an error occurs
                item['productname'] = ''

            try:
                item['reference'] = product.css(
                    'div.skuDesktop::text').get().replace(' [', '').replace(']', '')
            except AttributeError:
                # Set default value for reference when an error occurs
                item['reference'] = ''

            try:
                item['availability'] = product.css(
                    'div.stock.available span::text').get()
            except AttributeError:
                # Set default value for availability when an error occurs
                item['availability'] = ''

            try:
                item['brand'] = product.css(
                    'div.prdtBILCta a img').attrib['alt']
            except (AttributeError, KeyError):
                # Set default value for brand when an error occurs
                item['brand'] = ''

            try:
                item['imageUrl'] = product.css(
                    'span.product-image-wrapper img').attrib['src']
            except (AttributeError, KeyError):
                item['imageUrl'] = ''

            yield item

        next_page = response.css('a.action.next::attr(href)').extract_first()
        if next_page:

            yield response.follow(next_page, callback=self.parse)
