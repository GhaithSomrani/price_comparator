from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import logging

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "product_comparator"

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
products_collection = db['products']

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def add_price_modification_history():
    """
    Add price modification history to random products over the last 30 days.
    - Randomly selects 20-80 products per day
    - Changes price by -8% to +8%
    - Creates modification records for each day in the last 30 days
    """
    logger.info("Starting to add price modification history...")

    # Get all products from database
    all_products = list(products_collection.find({}))
    total_products = len(all_products)

    if total_products == 0:
        logger.warning("No products found in database!")
        return

    logger.info(f"Found {total_products} products in database")

    # Process each day for the last 30 days
    total_modifications = 0

    for day_offset in range(30, 0, -1):  # 30 days ago to 1 day ago
        # Calculate the modification date
        modification_date = datetime.now() - timedelta(days=day_offset)
        modification_date = modification_date.replace(
            hour=random.randint(8, 20),  # Random hour between 8 AM and 8 PM
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
            microsecond=0
        )

        # Randomly select number of products to modify (20 to 80)
        num_products_to_modify = random.randint(20, min(80, total_products))

        # Randomly select products
        selected_products = random.sample(all_products, num_products_to_modify)

        logger.info(f"Day -{day_offset}: Modifying {num_products_to_modify} products on {modification_date.strftime('%Y-%m-%d %H:%M:%S')}")

        # Modify each selected product
        for product in selected_products:
            product_id = product['_id']
            current_price = product.get('Price', 0)

            if current_price <= 0:
                continue

            # Calculate random percentage change (-8% to +8%)
            percentage_change = random.uniform(-8, 8)

            # Calculate old price (reverse the percentage to get original)
            # If current price is after change, old price = current / (1 + percentage/100)
            # But we want to add history, so old_price is current, new_price is calculated
            old_price = current_price
            new_price = round(old_price * (1 + percentage_change / 100), 2)

            # Create modification record
            modification_record = {
                'dateModification': modification_date,
                'oldPrice': old_price,
                'newPrice': new_price,
                'percentageChange': round(percentage_change, 2)
            }

            # Add modification to product's Modifications array
            result = products_collection.update_one(
                {'_id': product_id},
                {
                    '$push': {
                        'Modifications': modification_record
                    }
                }
            )

            if result.modified_count > 0:
                total_modifications += 1

        logger.info(f"Day -{day_offset}: Successfully added {num_products_to_modify} modifications")

    logger.info(f"Completed! Total modifications added: {total_modifications}")
    logger.info(f"Average modifications per day: {total_modifications / 30:.2f}")


def clear_all_modifications():
    """
    Clear all modification history from all products.
    Use this to reset before running add_price_modification_history again.
    """
    logger.info("Clearing all modifications...")

    result = products_collection.update_many(
        {},
        {
            '$set': {
                'Modifications': []
            }
        }
    )

    logger.info(f"Cleared modifications from {result.modified_count} products")


def get_modification_stats():
    """
    Get statistics about modifications in the database.
    """
    logger.info("Calculating modification statistics...")

    pipeline = [
        {
            '$project': {
                'Designation': 1,
                'modifications_count': {'$size': {'$ifNull': ['$Modifications', []]}}
            }
        },
        {
            '$group': {
                '_id': None,
                'total_products': {'$sum': 1},
                'total_modifications': {'$sum': '$modifications_count'},
                'avg_modifications': {'$avg': '$modifications_count'},
                'max_modifications': {'$max': '$modifications_count'},
                'min_modifications': {'$min': '$modifications_count'}
            }
        }
    ]

    result = list(products_collection.aggregate(pipeline))

    if result:
        stats = result[0]
        logger.info(f"Total products: {stats.get('total_products', 0)}")
        logger.info(f"Total modifications: {stats.get('total_modifications', 0)}")
        logger.info(f"Average modifications per product: {stats.get('avg_modifications', 0):.2f}")
        logger.info(f"Max modifications on a product: {stats.get('max_modifications', 0)}")
        logger.info(f"Min modifications on a product: {stats.get('min_modifications', 0)}")
    else:
        logger.info("No statistics available")


if __name__ == '__main__':
    print("=" * 60)
    print("Product Modification History Generator")
    print("=" * 60)
    print()
    print("Options:")
    print("1. Add price modification history (last 30 days)")
    print("2. Clear all modifications")
    print("3. Get modification statistics")
    print()

    choice = input("Enter your choice (1-3): ").strip()

    if choice == '1':
        confirm = input("This will add modifications to 20-80 random products per day for 30 days. Continue? (yes/no): ").strip().lower()
        if confirm == 'yes':
            add_price_modification_history()
        else:
            print("Operation cancelled.")

    elif choice == '2':
        confirm = input("This will clear ALL modifications from ALL products. Are you sure? (yes/no): ").strip().lower()
        if confirm == 'yes':
            clear_all_modifications()
        else:
            print("Operation cancelled.")

    elif choice == '3':
        get_modification_stats()

    else:
        print("Invalid choice!")

    print()
    print("Done!")
