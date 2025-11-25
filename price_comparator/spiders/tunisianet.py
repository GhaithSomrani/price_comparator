import scrapy
from datetime import datetime
from price_comparator.items import TunisianetItem
import re


class TunisianetSpider(scrapy.Spider):
    """
    Tunisianet spider for extracting product data.
    Updated to match API database schema with proper field extraction.
    """

    now = datetime.now()
    Nowdate = now.strftime("%Y-%m-%d %H:%M:%S")
    current_time = now.strftime("%Y_%m_%d_%H_%M_%S")

    name = "tunisianet"  # Changed to lowercase for consistency

    custom_settings = {
        "FEEDS": {
            f"dataproduct/TunisianetProduct_{current_time}.json": {
                "format": "json",
                "overwrite": True,
            }
        },
        "COOKIES_ENABLED": True,
        "COOKIES_DEBUG": True,
        # Use the unified ProductPipeline
        "ITEM_PIPELINES": {
            "price_comparator.pipelines.ProductPipeline": 300,
        },
        "CONCURRENT_REQUESTS": 10000,
        # "DOWNLOAD_DELAY": 0.5,
    }

    # Start from sitemap to get all categories
    start_urls = ["https://www.tunisianet.com.tn/sitemap"]

    def parse(self, response):
        """Parse sitemap to extract category links"""
        categorys = response.xpath('//a[contains(@id,"category-page")]')
        self.logger.info(f"Found {len(categorys)} categories")

        for category in categorys:
            try:
                category_name = category.css("a::text").get()
                if category_name:
                    category_name = category_name.strip().replace("\n", "")

                link = category.attrib.get("href", "")

                if link:
                    # You can filter specific categories here if needed
                    # For now, scraping all categories
                    # Uncomment the line below to scrape only "Accueil" category
                    # if category_name == 'Accueil':
                    self.logger.info(f"Scraping category: {category_name}")
                    yield scrapy.Request(link, callback=self.parse_category)

            except Exception as e:
                self.logger.error(f"Error parsing category: {e}")

    def parse_category(self, response):
        """Parse category page to extract product listings"""
        articles = response.css("article.product-miniature.js-product-miniature")
        self.logger.info(f"Found {len(articles)} products on {response.url}")

        for article in articles:
            item = TunisianetItem()

            try:
                # Extract product URL
                url = article.css("h2.product-title a::attr(href)").get()
                if url:
                    item["Url"] = url.strip()
                else:
                    continue  # Skip if no URL

                # Extract product name/designation
                productname = article.css("h2.product-title a::text").get()
                item["productname"] = productname.strip() if productname else ""

                # Extract product reference (remove brackets)
                reference = article.css("span.product-reference::text").get()
                if reference:
                    item["reference"] = (
                        reference.replace("[", "").replace("]", "").strip()
                    )
                else:
                    item["reference"] = ""

                # Extract short description
                description = article.css('div[itemprop="description"]').get()
                item["description"] = description.strip() if description else ""

                # Extract price
                price_text = article.css("span.price::text").get()
                if price_text:
                    # Remove currency and convert to float
                    # Format: "0,450 DT" or "1 234,567 DT"
                    price_cleaned = (
                        price_text.replace("DT", "")
                        .replace("\xa0", "")
                        .replace(" ", "")
                        .replace(",", ".")
                        .strip()
                    )
                    try:
                        item["price"] = float(price_cleaned)
                    except ValueError:
                        self.logger.warning(f"Could not parse price: {price_text}")
                        item["price"] = 0.0
                else:
                    item["price"] = 0.0

                # Extract brand from manufacturer logo
                brand_img = article.css("img.manufacturer-logo::attr(alt)").get()
                item["brand"] = brand_img.strip() if brand_img else "Unknown"

                # Extract availability/stock status
                # Try multiple selectors for stock availability
                availability = (
                    article.css("div#stock_availability span::text").get()
                    or article.css("span.in-stock::text").get()
                    or article.css("span.out-of-stock::text").get()
                    or ""
                )
                item["availability"] = (
                    availability.strip() if availability else "Unknown"
                )

                # Extract image URL
                image_url = (
                    article.css(
                        "img.center-block.img-responsive::attr(data-full-size-image-url)"
                    ).get()
                    or article.css("img.center-block.img-responsive::attr(src)").get()
                    or ""
                )
                item["imageUrl"] = image_url.strip() if image_url else ""

                # Extract basic category from URL (will be improved by visiting product page)
                basic_category = self._extract_category_from_url(url)
                item["category"] = basic_category
                item["subcategory"] = ""

                # Link field (for compatibility)
                item["link"] = url
                item["name"] = productname.strip() if productname else ""

                # Follow to product detail page to get proper category/subcategory from breadcrumb
                # Pass the item as meta to continue processing after breadcrumb extraction
                yield scrapy.Request(
                    url,
                    callback=self.parse_product_detail,
                    meta={"item": item},
                    priority=1,
                )

            except Exception as e:
                self.logger.error(f"Error parsing product in article: {e}")
                continue

        # Follow pagination
        try:
            next_page = response.css("a.next.js-search-link::attr(href)").get()
            if next_page:
                self.logger.info(f"Following pagination: {next_page}")
                yield response.follow(next_page, callback=self.parse_category)
        except Exception as e:
            self.logger.info(f"No more pages or error in pagination: {e}")

    def parse_product_detail(self, response):
        """Parse product detail page to extract category/subcategory from breadcrumb"""
        item = response.meta["item"]

        try:
            # Extract breadcrumb items
            breadcrumb_items = response.css(
                'nav.breadcrumb ol li[itemprop="itemListElement"] span[itemprop="name"]::text'
            ).getall()

            # Remove 'Accueil' (Home) if present
            if breadcrumb_items and breadcrumb_items[0].strip().lower() == "accueil":
                breadcrumb_items = breadcrumb_items[1:]

            # Remove the last item (product name)
            if breadcrumb_items and len(breadcrumb_items) > 0:
                breadcrumb_items = breadcrumb_items[:-1]

            # Extract category and subcategory from breadcrumb
            if len(breadcrumb_items) >= 1:
                item["category"] = breadcrumb_items[0].strip()

            if len(breadcrumb_items) >= 2:
                # Use the last category level as subcategory
                item["subcategory"] = breadcrumb_items[-1].strip()

            self.logger.debug(f"Extracted breadcrumb: {breadcrumb_items}")

        except Exception as e:
            self.logger.warning(f"Error extracting breadcrumb from {response.url}: {e}")
            # Keep the URL-based category if breadcrumb fails

        yield item

    def _extract_category_from_url(self, url):
        """
        Extract category from product URL.
        URL format: https://www.tunisianet.com.tn/category-name/product-id-product-name.html
        Example: https://www.tunisianet.com.tn/fourniture-stylos-feutres-rollers-tunisie/57526-stylo.html
        Returns: "Fourniture Stylos Feutres Rollers"
        """
        try:
            # Split URL and get the category part (index 3)
            parts = url.split("/")
            if len(parts) > 3:
                category_slug = parts[3]
                # Remove '-tunisie' suffix and replace dashes with spaces
                category = (
                    category_slug.replace("-tunisie", "").replace("-", " ").title()
                )
                return category
            return "Uncategorized"
        except Exception as e:
            self.logger.error(f"Error extracting category from URL {url}: {e}")
            return "Uncategorized"
