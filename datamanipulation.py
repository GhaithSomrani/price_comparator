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
    - Only selects products with price > 30
    - Randomly selects 20-80 products per day
    - Creates fake modification history (current price stays the same)
    - Old prices are integers and multiples of 5
    - Creates modification records for each day in the last 30 days
    """
    logger.info("Starting to add price modification history...")

    # Get all products from database with price > 30
    all_products = list(products_collection.find({'Price': {'$gt': 30}}))
    total_products = len(all_products)

    if total_products == 0:
        logger.warning("No products found in database with price > 30!")
        return

    logger.info(f"Found {total_products} products in database with price > 30")

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

            # Calculate old price by reversing the percentage
            # If new price is current price, old price = current / (1 + percentage/100)
            # This creates fake history: old_price -> changed by percentage -> current_price
            new_price = current_price  # New price is the current price
            calculated_old_price = current_price / (1 + percentage_change / 100)

            # Round to nearest multiple of 5 and convert to integer
            old_price = int(round(calculated_old_price / 5) * 5)

            # Ensure old price is positive and at least 5
            if old_price <= 0:
                old_price = int(round(current_price * 0.95 / 5) * 5)
            if old_price < 5:
                old_price = 5

            # Recalculate actual percentage change based on rounded old price
            actual_percentage_change = ((new_price - old_price) / old_price) * 100

            # Create modification record with old date
            # This represents: "on this old date, price changed from old_price to current_price"
            modification_record = {
                'dateModification': modification_date,
                'oldPrice': old_price,
                'newPrice': new_price,
                'percentageChange': round(actual_percentage_change, 2)
            }

            # Add modification to history ONLY (don't change current price)
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


def distribute_product_dates():
    """
    Randomly distribute product DateAjout across the last 30 days.
    - Step 1: Sets all products to -30 days ago
    - Step 2: Distributes them across the 30-day period (20-80 per day)
    - Step 3: Cleans up modifications that occurred before product was added

    This prevents products from showing as "new" but having old modifications.
    """
    logger.info("Starting to distribute product dates...")

    # Get all products from database
    all_products = list(products_collection.find({}))
    total_products = len(all_products)

    if total_products == 0:
        logger.warning("No products found in database!")
        return

    logger.info(f"Found {total_products} products in database")

    # Step 1: Set all products to -30 days ago
    logger.info("Step 1: Setting all products to -30 days ago...")
    thirty_days_ago = datetime.now() - timedelta(days=30)
    thirty_days_ago = thirty_days_ago.replace(hour=0, minute=0, second=0, microsecond=0)

    result = products_collection.update_many(
        {},
        {'$set': {'DateAjout': thirty_days_ago}}
    )
    logger.info(f"Set {result.modified_count} products to -30 days ago")

    # Step 2: Distribute products across 30 days
    logger.info("Step 2: Distributing products across 30 days...")

    # Shuffle products to randomize selection
    random.shuffle(all_products)

    # Track which products have been assigned
    product_index = 0
    total_updated = 0

    # Process each day for the last 30 days
    for day_offset in range(30, 0, -1):  # 30 days ago to 1 day ago
        # Calculate the date for this day
        date_ajout = datetime.now() - timedelta(days=day_offset)
        date_ajout = date_ajout.replace(
            hour=random.randint(6, 22),  # Random hour between 6 AM and 10 PM
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
            microsecond=0
        )

        # Randomly select number of products for this day (20 to 80)
        num_products_for_day = random.randint(20, min(80, total_products - product_index))

        if num_products_for_day <= 0:
            logger.info(f"Day -{day_offset}: No more products to assign")
            break

        logger.info(f"Day -{day_offset}: Assigning {num_products_for_day} products to {date_ajout.strftime('%Y-%m-%d %H:%M:%S')}")

        # Update products for this day
        day_updated = 0
        for i in range(num_products_for_day):
            if product_index >= total_products:
                break

            product = all_products[product_index]
            product_id = product['_id']

            # Add some randomness to the time for each product (within the same day)
            product_date = date_ajout + timedelta(
                hours=random.randint(0, 12),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )

            # Update the DateAjout field
            result = products_collection.update_one(
                {'_id': product_id},
                {
                    '$set': {
                        'DateAjout': product_date
                    }
                }
            )

            if result.modified_count > 0:
                day_updated += 1
                total_updated += 1

            product_index += 1

        logger.info(f"Day -{day_offset}: Successfully updated {day_updated} products")

    logger.info(f"Completed! Total products redistributed: {total_updated}")
    logger.info(f"Average products per day: {total_updated / 30:.2f}")

    # Check if there are remaining products (they will stay at -30 days)
    if product_index < total_products:
        remaining = total_products - product_index
        logger.info(f"{remaining} products remain at -30 days ago (not redistributed)")
        logger.info(f"Products at -30 days: {remaining}")
    else:
        logger.info("All products have been redistributed across the 30-day period")

    # Step 3: Clean up modifications that occurred before product was added
    logger.info("Step 3: Cleaning up invalid modifications...")
    cleaned_count = 0

    for product in all_products:
        product_id = product['_id']
        date_ajout = product.get('DateAjout')
        modifications = product.get('Modifications', [])

        if not date_ajout or not modifications:
            continue

        # Filter out modifications that happened before the product was added
        valid_modifications = [
            mod for mod in modifications
            if mod.get('dateModification') and mod.get('dateModification') >= date_ajout
        ]

        # If modifications were removed, update the product
        if len(valid_modifications) < len(modifications):
            products_collection.update_one(
                {'_id': product_id},
                {'$set': {'Modifications': valid_modifications}}
            )
            cleaned_count += 1

    logger.info(f"Cleaned invalid modifications from {cleaned_count} products")
    logger.info("Date distribution completed successfully!")


def get_dateajout_stats():
    """
    Get statistics about product DateAjout distribution.
    """
    logger.info("Calculating DateAjout statistics...")

    # Get date range
    thirty_days_ago = datetime.now() - timedelta(days=30)

    # Count products by date
    pipeline = [
        {
            '$match': {
                'DateAjout': {'$gte': thirty_days_ago}
            }
        },
        {
            '$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m-%d',
                        'date': '$DateAjout'
                    }
                },
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'_id': 1}}
    ]

    result = list(products_collection.aggregate(pipeline))

    total_count = products_collection.count_documents({})
    new_count = products_collection.count_documents({'DateAjout': {'$gte': thirty_days_ago}})

    logger.info(f"Total products in database: {total_count}")
    logger.info(f"Products added in last 30 days: {new_count}")
    logger.info(f"Products added per day:")

    for item in result:
        logger.info(f"  {item['_id']}: {item['count']} products")

    if result:
        avg_per_day = sum(item['count'] for item in result) / len(result)
        logger.info(f"Average products per day: {avg_per_day:.2f}")


if __name__ == '__main__':
    print("=" * 60)
    print("Product Data Manipulation Tool")
    print("=" * 60)
    print()
    print("Modification History Options:")
    print("1. Add price modification history (last 30 days)")
    print("2. Clear all modifications")
    print("3. Get modification statistics")
    print()
    print("Product Date Options:")
    print("4. Distribute product dates (last 30 days)")
    print("5. Get DateAjout statistics")
    print()

    choice = input("Enter your choice (1-5): ").strip()

    if choice == '1':
        confirm = input("This will add fake modification history to 20-80 random products (price > 30) per day for 30 days.\nOld prices will be integers and multiples of 5. Continue? (yes/no): ").strip().lower()
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

    elif choice == '4':
        confirm = input("This will:\n1. Set ALL products to -30 days ago\n2. Distribute 20-80 products per day across the 30-day period\n3. Clean up modifications that occurred before products were added\nContinue? (yes/no): ").strip().lower()
        if confirm == 'yes':
            distribute_product_dates()
        else:
            print("Operation cancelled.")

    elif choice == '5':
        get_dateajout_stats()

    else:
        print("Invalid choice!")

    print()
    print("Done!")
