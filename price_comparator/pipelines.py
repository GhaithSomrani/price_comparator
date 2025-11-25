import pymongo
from itemadapter import ItemAdapter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProductPipeline:
    """
    Unified pipeline for all stores that matches the Flask API database schema.
    Uses upsert to update existing products and tracks modifications.
    """

    # MongoDB Configuration
    MONGO_URI = "mongodb://localhost:27017/"
    DATABASE_NAME = "product_comparator"
    COLLECTION_NAME = "products"

    def __init__(self):
        self.client = pymongo.MongoClient(self.MONGO_URI)
        self.db = self.client[self.DATABASE_NAME]
        self.collection = self.db[self.COLLECTION_NAME]

        # Create indexes for better performance
        self.collection.create_index("Ref", unique=True)
        self.collection.create_index("Brand")
        self.collection.create_index("Category")
        self.collection.create_index("DateAjout")

        logger.info(f"Connected to MongoDB: {self.DATABASE_NAME}.{self.COLLECTION_NAME}")

    def process_item(self, item, spider):
        """Process and store item using upsert logic"""
        adapter = ItemAdapter(item)

        if adapter.get('reference'):
            # Determine store/company name from spider
            store_name = self._get_store_name(spider.name)

            # Prepare product data matching Flask API schema
            product_data = self._prepare_product_data(adapter, store_name)

            # Store or update in database
            self.upsert_product(product_data, adapter)

        return item

    def _get_store_name(self, spider_name):
        """Get store name from spider name"""
        store_mapping = {
            'tunisianet': 'Tunisianet',
            'mytek': 'MyTek',
        }
        return store_mapping.get(spider_name.lower(), spider_name.title())

    def _prepare_product_data(self, adapter, store_name):
        """
        Prepare product data to match Flask API schema:
        - Ref: Product reference
        - Designation: Product name
        - Price: Product price (float)
        - Brand: Brand name
        - Company: Store/company name
        - Category: Product category
        - Subcategory: Product subcategory (if available)
        - Stock: Stock status
        - DateAjout: Date added
        - Modifications: Array of modifications
        """

        # Parse price to float
        price = adapter.get("price", 0)
        if isinstance(price, str):
            # Remove currency symbols and convert to float
            price_str = price.replace('TND', '').replace('DT', '').replace(',', '').strip()
            try:
                price = float(price_str)
            except ValueError:
                price = 0.0

        # Prepare stock status
        availability = adapter.get('availability', 'Unknown')
        stock = self._parse_stock_status(availability)

        # Extract category and subcategory
        category = adapter.get('category', 'Uncategorized')
        subcategory = adapter.get('subcategory', '')

        # If subcategory is empty, try parsing from category
        if not subcategory and category:
            category, subcategory = self._parse_category(category)

        # Extract description
        description = adapter.get('description', '')
        if description:
            description = description.strip()

        return {
            'Ref': adapter.get('reference', '').strip(),
            'Designation': adapter.get('productname', '').strip(),
            'Description': description,
            'Price': price,
            'Brand': adapter.get('brand', 'Unknown').strip(),
            'Company': store_name,
            'Category': category,
            'Subcategory': subcategory,
            'Stock': stock,
            'Url': adapter.get('Url', ''),
            'ImageUrl': adapter.get('imageUrl', ''),
        }

    def _parse_stock_status(self, availability):
        """Parse availability text to stock status"""
        if not availability:
            return 'Unknown'

        availability_lower = str(availability).lower()

        if 'en stock' in availability_lower or 'disponible' in availability_lower or 'in stock' in availability_lower:
            return 'In Stock'
        elif 'rupture' in availability_lower or 'out of stock' in availability_lower or 'indisponible' in availability_lower:
            return 'Out of Stock'
        elif 'sur commande' in availability_lower or 'pre-order' in availability_lower:
            return 'On Order'
        else:
            return availability

    def _parse_category(self, category_full):
        """
        Parse category string into category and subcategory
        Example: "Electronics > Laptops" -> category="Electronics", subcategory="Laptops"
        """
        if not category_full:
            return 'Uncategorized', ''

        # Split by common separators
        parts = category_full.split('>')
        if len(parts) >= 2:
            category = parts[0].strip()
            subcategory = parts[1].strip()
        else:
            category = category_full.strip()
            subcategory = ''

        return category, subcategory

    def upsert_product(self, product_data, adapter):
        """
        Insert new product or update existing one with modification tracking.

        Logic:
        - If product doesn't exist: Insert new product with DateAjout
        - If product exists:
            - Check if price or stock changed
            - If changed: Add modification entry to Modifications array
            - Update product fields
        """
        ref = product_data['Ref']

        # Find existing product
        existing_product = self.collection.find_one({'Ref': ref})

        if existing_product:
            # Product exists - check for modifications
            modifications = existing_product.get('Modifications', [])

            # Check if price or stock changed
            price_changed = existing_product.get('Price') != product_data['Price']
            stock_changed = existing_product.get('Stock') != product_data['Stock']

            if price_changed or stock_changed:
                # Create modification entry
                modification = {
                    'dateModification': datetime.now(),
                    'oldPrice': existing_product.get('Price'),
                    'newPrice': product_data['Price'],
                    'oldStock': existing_product.get('Stock'),
                    'newStock': product_data['Stock'],
                }

                modifications.append(modification)

                logger.info(f"Product {ref} modified - Price: {modification['oldPrice']} -> {modification['newPrice']}, "
                          f"Stock: {modification['oldStock']} -> {modification['newStock']}")

            # Update product with new data
            update_data = {
                '$set': product_data,
                '$set': {'Modifications': modifications}
            }

            self.collection.update_one({'Ref': ref}, update_data)
            logger.info(f"Updated product: {ref}")

        else:
            # New product - insert with DateAjout
            product_data['DateAjout'] = datetime.now()
            product_data['Modifications'] = []

            self.collection.insert_one(product_data)
            logger.info(f"Inserted new product: {ref}")

    def close_spider(self, spider):
        """Close MongoDB connection when spider closes"""
        self.client.close()
        logger.info(f"Closed MongoDB connection for spider: {spider.name}")


# Legacy pipelines for backward compatibility (can be removed if not needed)
class TunisianetPipeline(ProductPipeline):
    """Backward compatible pipeline for Tunisianet"""
    pass


class MytekPipline(ProductPipeline):
    """Backward compatible pipeline for MyTek"""
    pass