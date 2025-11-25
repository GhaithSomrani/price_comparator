# Scrapy Spider Guide - Updated for API Integration

## Overview

The spiders have been updated to extract product data that matches the Flask API database schema. This guide explains how to use the updated spiders.

## What Changed

### Spider Names
- **Tunisianet**: `name = 'tunisianet'` (lowercase)
- **MyTek**: `name = 'mytek'` (lowercase)

### Pipeline Integration
Both spiders now use the unified `ProductPipeline` that:
- Matches the Flask API schema
- Implements upsert logic (insert new, update existing)
- Tracks price and stock modifications
- Stores in `products` collection

### Data Fields Extracted

Each spider extracts the following fields:

| Field | Description | Example |
|-------|-------------|---------|
| `reference` | Product reference/SKU | "8904228102916" |
| `productname` | Product name | "Stylo à Bille BIC Cello Tri Mate Vert" |
| `price` | Price (float) | 0.45 |
| `brand` | Brand name | "BIC" |
| `category` | Product category | "Fourniture Stylos Feutres Rollers" |
| `availability` | Stock status | "En stock" |
| `Url` | Product URL | Full product page URL |
| `imageUrl` | Product image URL | Full image URL |

### Improved Features

1. **Better Error Handling**: Comprehensive try-except blocks
2. **Logging**: Uses Scrapy's logger for better debugging
3. **Data Validation**: Skips products with missing critical data
4. **Price Parsing**: Handles various price formats (1,234.56 DT → 1234.56)
5. **Stock Normalization**: Maps availability text to standard statuses
6. **Category Extraction**: Extracts from URL structure

## Running the Spiders

### Prerequisites

1. Ensure MongoDB is running:
```bash
# Windows
net start MongoDB

# Linux/Mac
sudo systemctl start mongod
```

2. Navigate to the spider directory:
```bash
cd price_comparator
```

### Run Tunisianet Spider

```bash
# Basic run
scrapy crawl tunisianet

# With verbose logging
scrapy crawl tunisianet -s LOG_LEVEL=DEBUG

# Save to specific file
scrapy crawl tunisianet -o output_tunisianet.json
```

### Run MyTek Spider

```bash
# Basic run
scrapy crawl mytek

# With verbose logging
scrapy crawl mytek -s LOG_LEVEL=DEBUG

# Save to specific file
scrapy crawl mytek -o output_mytek.json
```

### Run Both Spiders

```bash
# Run sequentially
scrapy crawl tunisianet && scrapy crawl mytek

# Run in separate terminals (parallel)
# Terminal 1:
scrapy crawl tunisianet

# Terminal 2:
scrapy crawl mytek
```

## Understanding the Output

### Console Logging

You'll see logs like this:

```
2024-12-18 14:30:45 [tunisianet] INFO: Connected to MongoDB: product_comparator.products
2024-12-18 14:30:46 [tunisianet] INFO: Found 156 categories
2024-12-18 14:30:47 [tunisianet] INFO: Scraping category: Accueil
2024-12-18 14:30:48 [tunisianet] INFO: Found 24 products on https://www.tunisianet.com.tn/2-accueil
2024-12-18 14:30:49 [ProductPipeline] INFO: Inserted new product: 8904228102916
2024-12-18 14:30:50 [ProductPipeline] INFO: Product 1234567890 modified - Price: 99.99 -> 89.99, Stock: In Stock -> In Stock
2024-12-18 14:30:51 [tunisianet] INFO: Following pagination: https://www.tunisianet.com.tn/2-accueil?page=2
```

### JSON Output Files

JSON files are saved in `dataproduct/` directory:
- `TunisianetProduct_2024_12_18_14_30_45.json`
- `MytekProduct_2024_12_18_14_30_45.json`

### Database Storage

Products are stored in MongoDB:
- **Database**: `product_comparator`
- **Collection**: `products`
- **Schema**: Matches Flask API format

## Testing the Spiders

### Test with Sample HTML (Tunisianet)

Create a test script `test_tunisianet.py`:

```python
from scrapy.http import HtmlResponse, Request
from price_comparator.spiders.tunisianet import TunisianetSpider

# Read the sample HTML
with open('categorypages/tunisianet.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Create a mock response
url = 'https://www.tunisianet.com.tn/2-accueil'
request = Request(url=url)
response = HtmlResponse(url=url, request=request, body=html_content, encoding='utf-8')

# Create spider instance
spider = TunisianetSpider()

# Parse the response
items = list(spider.parse_category(response))

# Print results
print(f"Extracted {len(items)} items")
for i, item in enumerate(items[:3]):  # Print first 3
    print(f"\nItem {i+1}:")
    print(f"  Reference: {item.get('reference')}")
    print(f"  Name: {item.get('productname')}")
    print(f"  Price: {item.get('price')}")
    print(f"  Brand: {item.get('brand')}")
    print(f"  Stock: {item.get('availability')}")
    print(f"  Category: {item.get('category')}")
```

Run the test:
```bash
python test_tunisianet.py
```

### Verify Database Insertion

After running the spider, check MongoDB:

```javascript
// Connect to MongoDB
mongo

// Use database
use product_comparator

// Count products
db.products.count()

// View sample product
db.products.findOne()

// View product by reference
db.products.findOne({Ref: "8904228102916"})

// View products by store
db.products.find({Company: "Tunisianet"}).count()
db.products.find({Company: "MyTek"}).count()

// View products with modifications
db.products.find({Modifications: {$ne: []}}).count()
```

### Verify via Flask API

Start the Flask API:
```bash
cd ..
python app.py
```

Test endpoints:
```bash
# Get all products
curl http://localhost:5000/products

# Get newly added products
curl http://localhost:5000/products/new

# Get products by company
curl "http://localhost:5000/products?company=Tunisianet"

# Get products by brand
curl "http://localhost:5000/products?brand=BIC"
```

## Troubleshooting

### Spider Not Finding Products

**Issue**: `Found 0 products on page`

**Solutions**:
1. Check if website structure changed
2. Verify CSS selectors in spider code
3. Test with sample HTML files
4. Check if website blocks scrapers (use different user-agent)

### Price Parsing Errors

**Issue**: `Could not parse price: 1,234.56 DT`

**Solution**: Update price cleaning logic in spider:
```python
price_cleaned = price_text.replace('DT', '').replace(u'\xa0', '').replace(' ', '').replace(',', '.').strip()
```

### No Data in MongoDB

**Issue**: Products not appearing in database

**Solutions**:
1. Check MongoDB is running
2. Verify connection string in `settings.py`
3. Check pipeline is enabled
4. Look for errors in logs

### Duplicate Key Error

**Issue**: `E11000 duplicate key error collection: product_comparator.products index: Ref_1`

**Solution**: Product already exists - this is expected behavior. The pipeline will update the existing product.

### Reference Field Empty

**Issue**: Products inserted with empty `reference` field

**Solution**: Check selector for reference extraction:
```python
# Tunisianet
reference = article.css('span.product-reference::text').get()

# MyTek
reference = product.css('div.skuDesktop::text').get()
```

If still empty, the website might not display references on listing pages. Consider scraping individual product pages.

## Customization

### Scrape Specific Categories Only

Edit `tunisianet.py` in the `parse()` method:

```python
# Scrape only "Informatique" category
if category_name == 'Informatique':
    self.logger.info(f"Scraping category: {category_name}")
    yield scrapy.Request(link, callback=self.parse_category)
```

### Change Download Delay

Edit spider's `custom_settings`:

```python
custom_settings = {
    "DOWNLOAD_DELAY": 2.0,  # Wait 2 seconds between requests
    "CONCURRENT_REQUESTS": 4,  # Reduce concurrent requests
}
```

### Add More Fields

1. **Update `items.py`**:
```python
class TunisianetItem(Item):
    # ... existing fields ...
    description = Field()  # Add new field
    rating = Field()
```

2. **Update spider**:
```python
item['description'] = article.css('p.description::text').get()
item['rating'] = article.css('div.rating::attr(data-rating)').get()
```

3. **Update pipeline** (if needed):
```python
product_data['Description'] = adapter.get('description', '')
product_data['Rating'] = adapter.get('rating', 0)
```

## Performance Tips

### Faster Scraping

```bash
# Increase concurrent requests
scrapy crawl tunisianet -s CONCURRENT_REQUESTS=16

# Disable download delay
scrapy crawl tunisianet -s DOWNLOAD_DELAY=0

# Use both
scrapy crawl tunisianet -s CONCURRENT_REQUESTS=16 -s DOWNLOAD_DELAY=0
```

⚠️ **Warning**: Too aggressive settings might get you blocked!

### Memory Optimization

For large scrapes, disable JSON feed export:

```python
custom_settings = {
    'FEEDS': {},  # Disable file export
    # ... other settings
}
```

### Batch Processing

Process in batches using Scrapy's `CLOSESPIDER_ITEMCOUNT`:

```bash
# Scrape only 100 items
scrapy crawl tunisianet -s CLOSESPIDER_ITEMCOUNT=100
```

## Scheduled Scraping

### Using Cron (Linux/Mac)

Edit crontab:
```bash
crontab -e
```

Add daily scraping at 2 AM:
```
0 2 * * * cd /path/to/price_comparator && scrapy crawl tunisianet >> /var/log/tunisianet.log 2>&1
0 3 * * * cd /path/to/price_comparator && scrapy crawl mytek >> /var/log/mytek.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 2:00 AM)
4. Action: Start a program
   - Program: `scrapy`
   - Arguments: `crawl tunisianet`
   - Start in: `C:\path\to\price_comparator`

### Using Python Script

Create `run_scrapers.py`:

```python
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_spider(spider_name):
    """Run a spider and log results"""
    logger.info(f"Starting {spider_name} spider at {datetime.now()}")

    result = subprocess.run(
        ['scrapy', 'crawl', spider_name],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        logger.info(f"{spider_name} completed successfully")
    else:
        logger.error(f"{spider_name} failed: {result.stderr}")

    return result.returncode

if __name__ == '__main__':
    run_spider('tunisianet')
    run_spider('mytek')
```

Schedule with cron:
```
0 2 * * * python /path/to/run_scrapers.py
```

## Monitoring

### View Scraping Stats

Scrapy provides built-in stats:

```
2024-12-18 15:00:00 [scrapy.statscollectors] INFO: Dumping Scrapy stats:
{
    'downloader/request_count': 500,
    'downloader/response_count': 500,
    'item_scraped_count': 12000,
    'elapsed_time_seconds': 3600.0,
    'item_scraped_count': 12000,
}
```

### Monitor Database Growth

Create `monitor_db.py`:

```python
from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient("mongodb://localhost:27017/")
db = client["product_comparator"]
collection = db["products"]

# Total products
total = collection.count_documents({})
print(f"Total products: {total}")

# Products added today
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
today_count = collection.count_documents({'DateAjout': {'$gte': today}})
print(f"Products added today: {today_count}")

# Products modified today
modified_today = collection.count_documents({
    'Modifications.dateModification': {'$gte': today}
})
print(f"Products modified today: {modified_today}")

# By company
for company in ['Tunisianet', 'MyTek']:
    count = collection.count_documents({'Company': company})
    print(f"{company}: {count} products")
```

## Best Practices

1. **Always test with sample HTML first** before running full scrape
2. **Monitor logs** for errors and warnings
3. **Verify data quality** after scraping
4. **Use appropriate delays** to avoid being blocked
5. **Handle errors gracefully** with try-except blocks
6. **Log important events** for debugging
7. **Validate extracted data** before storing
8. **Update selectors** when website structure changes
9. **Run incrementally** (test with 1 category, then expand)
10. **Backup database** before major changes

## Next Steps

1. ✅ Test spiders with sample HTML
2. ✅ Run spiders on live websites
3. ✅ Verify data in MongoDB
4. ✅ Test Flask API endpoints
5. ✅ Set up scheduled scraping
6. ✅ Monitor for changes and errors
7. ✅ Add more stores as needed

## Support

For issues or questions:
- Check Scrapy documentation: https://docs.scrapy.org
- Review pipeline code in `pipelines.py`
- Check Flask API documentation in `README.md`
- Review pipeline updates in `PIPELINE_UPDATES.md`
