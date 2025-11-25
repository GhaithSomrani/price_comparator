import random
import scrapy
from datetime import datetime
from price_comparator.items import MytekItem


class MytekSpider(scrapy.Spider):
    """
    MyTek spider for extracting product data.
    Updated to match API database schema with proper field extraction.
    """
    now = datetime.now()
    Nowdate = now.strftime("%Y-%m-%d %H:%M:%S")
    current_time = now.strftime("%Y_%m_%d_%H_%M_%S")

    name = 'mytek'  # Changed to lowercase for consistency

    custom_settings = {
        'FEEDS': {
            f"dataproduct/MytekProduct_{current_time}.json": {
                "format": "json",
                "overwrite": True,
            }
        },
        'ROBOTSTXT_OBEY': False,
        "COOKIES_ENABLED": True,
        "COOKIES_DEBUG": True,
        # Use the unified ProductPipeline
        "ITEM_PIPELINES": {
            'price_comparator.pipelines.ProductPipeline': 300,
        },
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 1.0,
    }

    # Start URL for MyTek catalog search
    start_urls = [
        'https://www.mytek.tn/catalogsearch/result/index/?product_list_order=price&q=[',
    ]

    def start_requests(self):
        """Start requests with rotating user agents"""
        user_agent_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15'
        ]
        user_agent = random.choice(user_agent_list)
        self.logger.info(f"Using User-Agent: {user_agent}")

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
        """Parse product listing page"""
        products = response.css('li.item.product.product-item')
        self.logger.info(f"Found {len(products)} products on {response.url}")

        for product in products:
            item = MytekItem()

            try:
                # Extract product URL
                url = product.css('a.product-item-link::attr(href)').get()
                if url:
                    item['Url'] = url.strip()
                else:
                    continue  # Skip if no URL

                # Extract product name/designation
                productname = product.css('a.product-item-link::text').get()
                item['productname'] = productname.strip() if productname else ''

                # Extract product reference (remove brackets if present)
                reference = product.css('div.skuDesktop::text').get()
                if reference:
                    item['reference'] = reference.replace('[', '').replace(']', '').strip()
                else:
                    item['reference'] = ''

                # Extract short description (if available on listing page)
                description = product.css('div.product-item-description::text, div.product-description::text').get()
                item['description'] = description.strip() if description else ''

                # Extract price
                price_selector = product.css('span[data-price-type="finalPrice"]::attr(data-price-amount)').get()
                if price_selector:
                    try:
                        item['price'] = float(price_selector)
                    except ValueError:
                        self.logger.warning(f"Could not parse price: {price_selector}")
                        item['price'] = 0.0
                else:
                    item['price'] = 0.0

                # Extract brand from image alt attribute
                brand_img = product.css('div.prdtBILCta a img::attr(alt)').get()
                item['brand'] = brand_img.strip() if brand_img else 'Unknown'

                # Extract availability/stock status
                availability = product.css('div.stock.available span::text').get()
                if not availability:
                    availability = product.css('div.stock span::text').get()
                item['availability'] = availability.strip() if availability else 'Unknown'

                # Extract image URL
                image_url = product.css('span.product-image-wrapper img::attr(src)').get()
                item['imageUrl'] = image_url.strip() if image_url else ''

                # Extract category from URL
                item['category'] = self._extract_category_from_url(url)
                item['subcategory'] = ''  # Can be enhanced later if needed

                # Link and name fields (for compatibility)
                item['link'] = url
                item['name'] = productname.strip() if productname else ''

                yield item

            except Exception as e:
                self.logger.error(f"Error parsing product: {e}")
                continue

        # Follow pagination
        next_page = response.css('a.action.next::attr(href)').get()
        if next_page:
            self.logger.info(f"Following pagination: {next_page}")
            yield response.follow(next_page, callback=self.parse)
        else:
            self.logger.info("No more pages to scrape")

    def _extract_category_from_url(self, url):
        """
        Extract category from product URL.
        MyTek URL format may vary, extract from breadcrumb or URL structure
        Example: https://www.mytek.tn/informatique/ordinateurs-portables/laptop.html
        Returns: "Informatique"
        """
        try:
            # Split URL and try to get category
            parts = url.split('/')
            # Find the part after domain (index 3)
            if len(parts) > 3:
                category_slug = parts[3]
                # Convert slug to readable format
                category = category_slug.replace('-', ' ').title()
                return category
            return 'Uncategorized'
        except Exception as e:
            self.logger.error(f"Error extracting category from URL {url}: {e}")
            return 'Uncategorized'
