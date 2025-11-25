# Price Comparator Scrapy Project

This Scrapy project scrapes product data from multiple e-commerce stores and stores it in MongoDB with proper modification tracking.

## Features

- **Unified Pipeline**: Single pipeline (`ProductPipeline`) that works with all spiders
- **Schema Compatibility**: Matches the Flask API database schema for seamless integration
- **Upsert Logic**: Automatically updates existing products or inserts new ones
- **Modification Tracking**: Tracks price and stock changes in a `Modifications` array
- **Multi-Store Support**: Currently supports Tunisianet and MyTek

## Database Schema

Products are stored in the following format:

```json
{
  "_id": "ObjectId",
  "Ref": "product_reference",
  "Designation": "product_name",
  "Price": 99.99,
  "Brand": "brand_name",
  "Company": "store_name",
  "Category": "category_name",
  "Subcategory": "subcategory_name",
  "Stock": "In Stock",
  "Url": "product_url",
  "ImageUrl": "image_url",
  "DateAjout": "2024-12-18T14:00:00",
  "Modifications": [
    {
      "dateModification": "2024-12-18T15:00:00",
      "oldPrice": 89.99,
      "newPrice": 99.99,
      "oldStock": "Out of Stock",
      "newStock": "In Stock"
    }
  ]
}
```

## Installation

1. Install Scrapy and dependencies:
```bash
pip install scrapy pymongo
```

2. Configure MongoDB connection in `settings.py`:
```python
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "product_comparator"
MONGO_COLLECTION = "products"
```

## Running the Scrapers

Navigate to the project directory and run:

```bash
# Run Tunisianet spider
scrapy crawl tunisianet

# Run MyTek spider
scrapy crawl mytek

# Run with custom settings
scrapy crawl tunisianet -s LOG_LEVEL=DEBUG
```

## Pipeline Features

### 1. Product Data Normalization

The pipeline automatically normalizes data from different stores:

- **Price Parsing**: Converts string prices with currency symbols to float
- **Stock Status**: Maps availability text to standard statuses:
  - "In Stock" (en stock, disponible)
  - "Out of Stock" (rupture, indisponible)
  - "On Order" (sur commande, pre-order)
- **Category/Subcategory**: Splits category strings (e.g., "Electronics > Laptops")

### 2. Upsert Logic

When a product is scraped:

**If product doesn't exist:**
- Insert new product with current timestamp in `DateAjout`
- Initialize empty `Modifications` array

**If product exists:**
- Compare current price and stock with existing data
- If changed: Add modification entry to `Modifications` array
- Update product fields with new data

### 3. Modification Tracking

Each modification entry contains:
- `dateModification`: Timestamp of change
- `oldPrice`: Previous price
- `newPrice`: New price
- `oldStock`: Previous stock status
- `newStock`: New stock status

### 4. Database Indexing

The pipeline automatically creates indexes on:
- `Ref` (unique) - For fast lookups and preventing duplicates
- `Brand` - For filtering by brand
- `Category` - For filtering by category
- `DateAjout` - For date-based queries

## Configuration

### MongoDB Settings

Edit `settings.py` to configure MongoDB:

```python
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "product_comparator"
MONGO_COLLECTION = "products"
```

### Pipeline Configuration

The pipeline is enabled in `settings.py`:

```python
ITEM_PIPELINES = {
    "price_comparator.pipelines.ProductPipeline": 300,
}
```

### Logging

Logging is configured in `settings.py`:

```python
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
```

## Adding New Spiders

To add a new store:

1. Create a new spider in `spiders/` directory
2. Use the same item structure (`TunisianetItem` or `MytekItem`)
3. Add store mapping in `pipelines.py`:

```python
def _get_store_name(self, spider_name):
    store_mapping = {
        'tunisianet': 'Tunisianet',
        'mytek': 'MyTek',
        'newstore': 'NewStore',  # Add your store here
    }
    return store_mapping.get(spider_name.lower(), spider_name.title())
```

## Integration with Flask API

The data stored by this scraper is fully compatible with the Flask API endpoints:

- `/products` - Query all products
- `/products/new` - Get newly added products
- `/products/modified` - Get recently modified products
- `/filter` - Get filter values
- `/stats` - Get statistics

## Monitoring

The pipeline logs important events:

- **INFO**: Product insertions and updates
- **INFO**: Price/stock changes
- **ERROR**: Database connection issues
- **ERROR**: Data validation errors

Example log output:

```
2024-12-18 14:30:45 [ProductPipeline] INFO: Inserted new product: REF123
2024-12-18 14:30:46 [ProductPipeline] INFO: Product REF456 modified - Price: 99.99 -> 89.99, Stock: In Stock -> Out of Stock
```

## Troubleshooting

### Duplicate Key Error

If you get a duplicate key error, the product reference already exists. The upsert logic should handle this, but if it persists:

```python
# Drop the index and recreate
db.products.dropIndex("Ref_1")
```

### Connection Errors

Check MongoDB is running:

```bash
# On Linux/Mac
sudo systemctl status mongod

# On Windows
net start MongoDB
```

### Price Parsing Issues

If prices are not parsed correctly, update the `_prepare_product_data` method in `pipelines.py` to handle your specific currency format.

## File Structure

```
price_comparator/
├── price_comparator/
│   ├── spiders/
│   │   ├── __init__.py
│   │   ├── tunisianet.py
│   │   └── mytek.py
│   ├── __init__.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   └── settings.py
├── scrapy.cfg
└── README.md
```

## Notes

- All text searches in the Flask API are case-insensitive
- Date formats are ISO 8601
- The pipeline uses the same database and collection as the Flask API
- Product references (`Ref`) must be unique
- Modifications are tracked indefinitely (consider adding cleanup logic for old modifications)
