import scrapy
from datetime import datetime
from price_comparator.items import TunisianetItem


class TunisianetSpider(scrapy.Spider):
    now = datetime.now()
    Nowdate = now.strftime("%Y-%m-%d %H:%M:%S")

    current_time = now.strftime("%Y_%m_%d_%H_%M_%S")

    name = 'Tunisianet'
    custom_settings = {
        'FEEDS': {
            "dataproduct/TunisinetProduct"+current_time+".json": {
                "format": "json",
                "overwrite": True,
            }
        },
        "COOKIES_ENABLED": True,
        "COOKIES_DEBUG": True,
        "ITEM_PIPELINES": {
            'price_comparator.pipelines.TunisianetPipeline': 300,
        }


    }
    start_urls = ['https://www.tunisianet.com.tn/sitemap', ]

    def parse(self, response):

        categorys = response.xpath('//a[contains(@id,"category-page")]')
        print(len(categorys))
        item = TunisianetItem()
        for category in categorys:

            item['name'] = category.css('a::text').get().replace(
                '  ', '').replace('\n', '')
            item['link'] = category.attrib['href']

            link = category.attrib['href']
            url = response.urljoin(link)
            if item['name'] == 'Accueil':
                yield scrapy.Request(url, callback=self.parse_product)

    def parse_product(self, response):
        item = TunisianetItem()

        articles = response.css(
            'article.product-miniature.js-product-miniature.col-xs-12.propadding')
        for article in articles:
            
            try:
                url = article.css('h2>a').attrib['href']
                item['Url'] = url

                m = article.css('span.price::text').get().replace(' DT', '').replace(u'\xa0', '').replace(',', '.')
                price = float(m)
                item['price'] = price
            except (AttributeError, ValueError):
                item['Url'] = ''
                item['price'] = None  # Set default value for price when an error occurs

            try:
                item['category'] = url.split('/')[3].replace('-', ' ').replace(' tunisie', '')
            except IndexError:
                item['category'] = ''  # Set default value for category when an error occurs

            try:
                item['productname'] = article.css('h2>a::text').get()
            except AttributeError:
                item['productname'] = ''  # Set default value for productname when an error occurs

            try:
                item['reference'] = article.css('span.product-reference::text').get().replace('[', '').replace(']', '')
            except AttributeError:
                item['reference'] = ''  # Set default value for reference when an error occurs

            try:
                item['availability'] = response.css('#stock_availability > span::text').get()
            except AttributeError:
                item['availability'] = ''  # Set default value for availability when an error occurs

            try:
                item['brand'] = article.css('img.img.img-thumbnail.manufacturer-logo').attrib['alt']
            except (AttributeError, KeyError):
                item['brand'] = ''  # Set default value for brand when an error occurs

            try:
                item['imageUrl'] = article.css('a>img.center-block.img-responsive').attrib['data-full-size-image-url']
            except (AttributeError, KeyError):
                item['imageUrl'] = ''  # Set default value for imageUrl when an error occurs

            yield item

        next_page = response.css('a.next.js-search-link').attrib['href']
        print(next_page)
        yield response.follow(next_page, callback=self.parse_product)
