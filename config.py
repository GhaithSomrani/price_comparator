"""
Configuration file for Flask application
Update these settings according to your MongoDB setup
"""

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "your_database_name"
COLLECTION_NAME = "products"

# Flask Configuration
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000

# Pagination Defaults
DEFAULT_PAGE = 1
DEFAULT_PRODUCTS_PER_PAGE = 10

# Date Range Defaults (in days)
DEFAULT_NEW_PRODUCTS_DAYS = 1
DEFAULT_MODIFIED_PRODUCTS_DAYS = 2
DEFAULT_STATS_DAYS = 30
