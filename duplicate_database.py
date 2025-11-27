from pymongo import MongoClient
import logging

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
SOURCE_DATABASE = "product_comparator"
TARGET_DATABASE = "product_comparator_backup"

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def duplicate_database(source_db_name, target_db_name):
    """
    Duplicate a MongoDB database by copying all collections and documents.
    """
    try:
        logger.info(f"Starting database duplication from '{source_db_name}' to '{target_db_name}'...")

        # Connect to MongoDB
        client = MongoClient(MONGO_URI)

        # Get source and target databases
        source_db = client[source_db_name]
        target_db = client[target_db_name]

        # Get all collection names from source database
        collections = source_db.list_collection_names()

        if not collections:
            logger.warning(f"No collections found in source database '{source_db_name}'")
            return

        logger.info(f"Found {len(collections)} collection(s): {collections}")

        total_documents = 0

        # Copy each collection
        for collection_name in collections:
            logger.info(f"Copying collection '{collection_name}'...")

            source_collection = source_db[collection_name]
            target_collection = target_db[collection_name]

            # Drop target collection if it exists
            target_collection.drop()

            # Get all documents from source collection
            documents = list(source_collection.find({}))
            doc_count = len(documents)

            if doc_count > 0:
                # Insert documents into target collection
                target_collection.insert_many(documents)
                logger.info(f"Copied {doc_count} documents to '{collection_name}'")
                total_documents += doc_count
            else:
                logger.info(f"Collection '{collection_name}' is empty")

            # Copy indexes
            indexes = list(source_collection.list_indexes())
            for index in indexes:
                if index['name'] != '_id_':  # Skip default _id index
                    try:
                        index_keys = list(index['key'].items())
                        target_collection.create_index(index_keys, name=index['name'])
                        logger.info(f"Created index '{index['name']}' on '{collection_name}'")
                    except Exception as e:
                        logger.warning(f"Failed to create index '{index['name']}': {str(e)}")

        logger.info(f"Database duplication completed!")
        logger.info(f"Total documents copied: {total_documents}")
        logger.info(f"Target database: '{target_db_name}'")

        client.close()

    except Exception as e:
        logger.error(f"Error during database duplication: {str(e)}")
        raise


def list_databases():
    """
    List all databases in MongoDB server.
    """
    try:
        client = MongoClient(MONGO_URI)
        databases = client.list_database_names()

        logger.info("Available databases:")
        for db in databases:
            logger.info(f"  - {db}")

        client.close()
    except Exception as e:
        logger.error(f"Error listing databases: {str(e)}")


def drop_database(db_name):
    """
    Drop a database (use with caution!).
    """
    try:
        client = MongoClient(MONGO_URI)
        client.drop_database(db_name)
        logger.info(f"Database '{db_name}' has been dropped")
        client.close()
    except Exception as e:
        logger.error(f"Error dropping database: {str(e)}")


def restore_backup():
    """
    Restore the database from backup.
    Copies data from backup database back to the main database.
    """
    try:
        logger.info(f"Starting database restore from '{TARGET_DATABASE}' to '{SOURCE_DATABASE}'...")

        # Connect to MongoDB
        client = MongoClient(MONGO_URI)

        # Check if backup database exists
        if TARGET_DATABASE not in client.list_database_names():
            logger.error(f"Backup database '{TARGET_DATABASE}' does not exist!")
            logger.info("Available databases:")
            for db in client.list_database_names():
                logger.info(f"  - {db}")
            client.close()
            return

        # Get backup and target databases
        backup_db = client[TARGET_DATABASE]
        target_db = client[SOURCE_DATABASE]

        # Get all collection names from backup database
        collections = backup_db.list_collection_names()

        if not collections:
            logger.warning(f"No collections found in backup database '{TARGET_DATABASE}'")
            client.close()
            return

        logger.info(f"Found {len(collections)} collection(s) in backup: {collections}")

        total_documents = 0

        # Copy each collection from backup to main
        for collection_name in collections:
            logger.info(f"Restoring collection '{collection_name}'...")

            backup_collection = backup_db[collection_name]
            target_collection = target_db[collection_name]

            # Drop target collection if it exists
            target_collection.drop()

            # Get all documents from backup collection
            documents = list(backup_collection.find({}))
            doc_count = len(documents)

            if doc_count > 0:
                # Insert documents into target collection
                target_collection.insert_many(documents)
                logger.info(f"Restored {doc_count} documents to '{collection_name}'")
                total_documents += doc_count
            else:
                logger.info(f"Collection '{collection_name}' is empty")

            # Copy indexes
            indexes = list(backup_collection.list_indexes())
            for index in indexes:
                if index['name'] != '_id_':  # Skip default _id index
                    try:
                        index_keys = list(index['key'].items())
                        target_collection.create_index(index_keys, name=index['name'])
                        logger.info(f"Created index '{index['name']}' on '{collection_name}'")
                    except Exception as e:
                        logger.warning(f"Failed to create index '{index['name']}': {str(e)}")

        logger.info(f"Database restore completed!")
        logger.info(f"Total documents restored: {total_documents}")
        logger.info(f"Database '{SOURCE_DATABASE}' has been restored from '{TARGET_DATABASE}'")

        client.close()

    except Exception as e:
        logger.error(f"Error during database restore: {str(e)}")
        raise


if __name__ == '__main__':
    print("=" * 60)
    print("MongoDB Database Management Tool")
    print("=" * 60)
    print()
    print("Backup Options:")
    print("1. Create backup (product_comparator -> product_comparator_backup)")
    print("2. Restore from backup (product_comparator_backup -> product_comparator)")
    print()
    print("Advanced Options:")
    print("3. Duplicate database (custom names)")
    print("4. List all databases")
    print("5. Drop a database")
    print()

    choice = input("Enter your choice (1-5): ").strip()

    if choice == '1':
        print()
        print(f"Source database: {SOURCE_DATABASE}")
        print(f"Target database: {TARGET_DATABASE}")
        print("This will create a backup of your current database.")
        confirm = input("Proceed with backup? (yes/no): ").strip().lower()

        if confirm == 'yes':
            duplicate_database(SOURCE_DATABASE, TARGET_DATABASE)
        else:
            print("Operation cancelled.")

    elif choice == '2':
        print()
        print(f"Backup database: {TARGET_DATABASE}")
        print(f"Main database: {SOURCE_DATABASE}")
        print("WARNING: This will replace your current database with the backup!")
        confirm = input("Proceed with restore? (yes/no): ").strip().lower()

        if confirm == 'yes':
            restore_backup()
        else:
            print("Operation cancelled.")

    elif choice == '3':
        print()
        source = input("Enter source database name: ").strip()
        target = input("Enter target database name: ").strip()

        if source and target:
            print()
            print(f"Source database: {source}")
            print(f"Target database: {target}")
            confirm = input("Proceed with duplication? (yes/no): ").strip().lower()

            if confirm == 'yes':
                duplicate_database(source, target)
            else:
                print("Operation cancelled.")
        else:
            print("Invalid database names!")

    elif choice == '4':
        list_databases()

    elif choice == '5':
        print()
        db_name = input("Enter database name to drop: ").strip()

        if db_name:
            confirm = input(f"Are you SURE you want to drop '{db_name}'? This cannot be undone! (yes/no): ").strip().lower()

            if confirm == 'yes':
                drop_database(db_name)
            else:
                print("Operation cancelled.")
        else:
            print("Invalid database name!")

    else:
        print("Invalid choice!")

    print()
    print("Done!")
