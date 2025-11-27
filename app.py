from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
import traceback

# Initialize Flask app
app = Flask(__name__)

# MongoDB Configuration
# TODO: Update with your MongoDB connection string
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "product_comparator"

# Configure MongoDB client with 5-minute timeout
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=300000,  # 5 minutes
    socketTimeoutMS=300000  # 5 minutes
)
db = client[DATABASE_NAME]
products_collection = db['products']

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
connection_logger = logging.getLogger('connection')
error_logger = logging.getLogger('error')


# ==================== /filter Endpoint ====================
@app.route('/filter', methods=['GET'])
def filter_endpoint():
    """
    Retrieves filter data based on search parameters for product information
    such as brand, stock, category, and subcategory.
    """
    try:
        # Log incoming request
        connection_logger.info(f"Accessed /filter endpoint with params: {request.args}")

        # Extract query parameters
        brand_search = request.args.get('brand', '')
        stock_search = request.args.get('stock', '')
        category_search = request.args.get('category', '')
        subcategory_search = request.args.get('subcategory', '')

        # Build match stage for aggregation pipeline
        match_stage = {}

        if brand_search:
            match_stage['Brand'] = {'$regex': brand_search, '$options': 'i'}
        if stock_search:
            match_stage['Stock'] = {'$regex': stock_search, '$options': 'i'}
        if category_search:
            match_stage['Category'] = {'$regex': category_search, '$options': 'i'}
        if subcategory_search:
            match_stage['Subcategory'] = {'$regex': subcategory_search, '$options': 'i'}

        # Build aggregation pipeline
        pipeline = []

        if match_stage:
            pipeline.append({'$match': match_stage})

        pipeline.append({
            '$group': {
                '_id': None,
                'brands': {'$addToSet': '$Brand'},
                'stocks': {'$addToSet': '$Stock'},
                'categories': {'$addToSet': '$Category'},
                'subcategories': {'$addToSet': '$Subcategory'}
            }
        })

        # Execute aggregation
        result = list(products_collection.aggregate(pipeline))

        # Format response
        if result:
            filters = {
                'brands': sorted([b for b in result[0].get('brands', []) if b]),
                'stocks': sorted([s for s in result[0].get('stocks', []) if s]),
                'categories': sorted([c for c in result[0].get('categories', []) if c]),
                'subcategories': sorted([sc for sc in result[0].get('subcategories', []) if sc])
            }
        else:
            filters = {
                'brands': [],
                'stocks': [],
                'categories': [],
                'subcategories': []
            }

        connection_logger.info("Successfully retrieved filter data")

        response = make_response(jsonify({'filters': filters}), 200)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        error_logger.error(f"Error in /filter endpoint: {str(e)}")
        error_logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# ==================== /products Endpoint ====================
@app.route('/products', methods=['GET'])
def products():
    """
    Retrieves a list of products from the database with filtering, sorting, and pagination options.
    This is a general endpoint without default date filters.
    """
    try:
        connection_logger.info(f"Accessed /products endpoint with params: {request.args}")

        # Extract query parameters
        ref = request.args.get('ref', '')
        designation = request.args.get('designation', '')
        price_min = request.args.get('price_min', type=float)
        price_max = request.args.get('price_max', type=float)
        brand = request.args.get('brand', '')
        stock = request.args.get('stock', '')
        company = request.args.get('company', '')
        category = request.args.get('category', '')
        subcategory = request.args.get('subcategory', '')
        dateajout_min = request.args.get('dateajout_min', '')
        dateajout_max = request.args.get('dateajout_max', '')
        datemodification_min = request.args.get('datemodification_min', '')
        datemodification_max = request.args.get('datemodification_max', '')
        sort_by = request.args.get('sort_by', 'dateajout')
        order = request.args.get('order', 'asc')
        page = request.args.get('page', 1, type=int)
        products_per_page = request.args.get('products_per_page', 10, type=int)

        # Build query filter
        query = {}

        # DateAjout filter (no default date range)
        if dateajout_min or dateajout_max:
            date_query = {}
            try:
                if dateajout_min:
                    min_date = datetime.fromisoformat(dateajout_min.replace('Z', '+00:00'))
                    min_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    date_query['$gte'] = min_date
                if dateajout_max:
                    max_date = datetime.fromisoformat(dateajout_max.replace('Z', '+00:00'))
                    max_date = max_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    date_query['$lte'] = max_date
                query['DateAjout'] = date_query
            except ValueError:
                return jsonify({'error': 'Invalid date format for dateajout'}), 400

        # Modification date filter (no default date range)
        if datemodification_min or datemodification_max:
            modification_query = {}
            try:
                if datemodification_min:
                    min_date = datetime.fromisoformat(datemodification_min.replace('Z', '+00:00'))
                    min_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    modification_query['$gte'] = min_date
                if datemodification_max:
                    max_date = datetime.fromisoformat(datemodification_max.replace('Z', '+00:00'))
                    max_date = max_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    modification_query['$lte'] = max_date
                query['Modifications.dateModification'] = modification_query
            except ValueError:
                return jsonify({'error': 'Invalid date format for modification dates'}), 400

        # Text filters (partial matches with case-insensitive regex)
        if ref:
            query['Ref'] = {'$regex': ref, '$options': 'i'}
        if designation:
            query['Designation'] = {'$regex': designation, '$options': 'i'}
        if brand:
            query['Brand'] = {'$regex': brand, '$options': 'i'}
        if stock:
            query['Stock'] = {'$regex': stock, '$options': 'i'}
        if company:
            query['Company'] = {'$regex': company, '$options': 'i'}
        if category:
            query['Category'] = {'$regex': category, '$options': 'i'}
        if subcategory:
            query['Subcategory'] = {'$regex': subcategory, '$options': 'i'}

        # Price filters
        if price_min is not None or price_max is not None:
            query['Price'] = {}
            if price_min is not None:
                query['Price']['$gte'] = price_min
            if price_max is not None:
                query['Price']['$lte'] = price_max

        # Sorting
        sort_field = sort_by if sort_by in ['price', 'dateajout', 'last_modification'] else 'dateajout'
        sort_field_map = {
            'price': 'Price',
            'dateajout': 'DateAjout',
            'last_modification': 'Modifications.dateModification'
        }
        sort_direction = 1 if order == 'asc' else -1

        # Calculate pagination
        skip = (page - 1) * products_per_page

        # Get total count
        total_products = products_collection.count_documents(query)
        total_pages = (total_products + products_per_page - 1) // products_per_page

        # Fetch products
        products = list(
            products_collection.find(query)
            .sort(sort_field_map[sort_field], sort_direction)
            .skip(skip)
            .limit(products_per_page)
        )

        # Convert ObjectId to string
        for product in products:
            product['_id'] = str(product['_id'])

        # Get additional statistics based on current query
        yesterday = datetime.now() - timedelta(days=1)
        two_days_ago = datetime.now() - timedelta(days=2)

        # Count new products (added in last 24 hours) that match the query
        total_new_products = products_collection.count_documents({
            **query,
            'DateAjout': {'$gte': yesterday}
        })

        # Count modified products (modified in last 2 days) that match the query
        total_modified_products = products_collection.count_documents({
            **query,
            'Modifications.dateModification': {'$gte': two_days_ago}
        })

        # Get stock status counts based on current query
        total_in_stock = products_collection.count_documents({
            **query,
            'Stock': {'$regex': '^in stock$', '$options': 'i'}
        })
        total_on_order = products_collection.count_documents({
            **query,
            'Stock': {'$regex': '^on order$', '$options': 'i'}
        })
        total_out_of_stock = products_collection.count_documents({
            **query,
            'Stock': {'$regex': '^out of stock$', '$options': 'i'}
        })

        response_data = {
            'total_products': total_products,
            'total_new_products': total_new_products,
            'total_modified_products': total_modified_products,
            'total_pages': total_pages,
            'current_page': page,
            'products_per_page': products_per_page,
            'stock_status': {
                'in_stock': total_in_stock,
                'on_order': total_on_order,
                'out_of_stock': total_out_of_stock
            },
            'products': products
        }

        connection_logger.info(f"Successfully retrieved {len(products)} products")

        response = make_response(jsonify(response_data), 200)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        error_logger.error(f"Error in /products endpoint: {str(e)}")
        error_logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# ==================== /products/new Endpoint ====================
@app.route('/products/new', methods=['GET'])
def products_new():
    """
    Retrieves a list of newly added products within the last day (or a custom date range).
    """
    try:
        connection_logger.info(f"Accessed /products/new endpoint with params: {request.args}")

        # Extract query parameters
        ref = request.args.get('ref', '')
        designation = request.args.get('designation', '')
        price_min = request.args.get('price_min', type=float)
        price_max = request.args.get('price_max', type=float)
        brand = request.args.get('brand', '')
        stock = request.args.get('stock', '')
        company = request.args.get('company', '')
        category = request.args.get('category', '')
        subcategory = request.args.get('subcategory', '')
        dateajout_min = request.args.get('dateajout_min', '')
        sort_by = request.args.get('sort_by', 'dateajout')
        order = request.args.get('order', 'asc')
        page = request.args.get('page', 1, type=int)
        products_per_page = request.args.get('products_per_page', 10, type=int)

        # Build query filter
        query = {}

        # Date filter - default to last day if not specified
        if dateajout_min:
            try:
                min_date = datetime.fromisoformat(dateajout_min.replace('Z', '+00:00'))
                min_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
                query['DateAjout'] = {'$gte': min_date}
            except ValueError:
                return jsonify({'error': 'Invalid date format for dateajout_min'}), 400
        else:
            # Default: last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            query['DateAjout'] = {'$gte': yesterday}

        # Text filters
        if ref:
            query['Ref'] = {'$regex': ref, '$options': 'i'}
        if designation:
            query['Designation'] = {'$regex': designation, '$options': 'i'}
        if brand:
            query['Brand'] = {'$regex': brand, '$options': 'i'}
        if stock:
            query['Stock'] = {'$regex': stock, '$options': 'i'}
        if company:
            query['Company'] = {'$regex': company, '$options': 'i'}
        if category:
            query['Category'] = {'$regex': category, '$options': 'i'}
        if subcategory:
            query['Subcategory'] = {'$regex': subcategory, '$options': 'i'}

        # Price filters
        if price_min is not None or price_max is not None:
            query['Price'] = {}
            if price_min is not None:
                query['Price']['$gte'] = price_min
            if price_max is not None:
                query['Price']['$lte'] = price_max

        # Sorting
        sort_field = sort_by if sort_by in ['price', 'dateajout', 'last_modification'] else 'dateajout'
        sort_field_map = {
            'price': 'Price',
            'dateajout': 'DateAjout',
            'last_modification': 'Modifications.dateModification'
        }
        sort_direction = 1 if order == 'asc' else -1

        # Calculate pagination
        skip = (page - 1) * products_per_page

        # Get total count
        total_products = products_collection.count_documents(query)
        total_pages = (total_products + products_per_page - 1) // products_per_page

        # Fetch products
        products = list(
            products_collection.find(query)
            .sort(sort_field_map[sort_field], sort_direction)
            .skip(skip)
            .limit(products_per_page)
        )

        # Convert ObjectId to string
        for product in products:
            product['_id'] = str(product['_id'])

        # Get stock status counts for new products
        in_stock_count = products_collection.count_documents({
            **query,
            'Stock': {'$regex': '^in stock$', '$options': 'i'}
        })
        on_order_count = products_collection.count_documents({
            **query,
            'Stock': {'$regex': '^on order$', '$options': 'i'}
        })
        out_of_stock_count = products_collection.count_documents({
            **query,
            'Stock': {'$regex': '^out of stock$', '$options': 'i'}
        })

        response_data = {
            'total_products': total_products,
            'total_pages': total_pages,
            'current_page': page,
            'products_per_page': products_per_page,
            'stock_status': {
                'in_stock': in_stock_count,
                'on_order': on_order_count,
                'out_of_stock': out_of_stock_count
            },
            'products': products
        }

        connection_logger.info(f"Successfully retrieved {len(products)} new products")

        response = make_response(jsonify(response_data), 200)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        error_logger.error(f"Error in /products/new endpoint: {str(e)}")
        error_logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# ==================== /products/modified Endpoint ====================
@app.route('/products/modified', methods=['GET'])
def products_modified():
    """
    Retrieves a list of products modified within the last two days (or a custom date range).
    Supports filtering, sorting, and pagination.
    """
    try:
        connection_logger.info(f"Accessed /products/modified endpoint with params: {request.args}")

        # Extract query parameters
        ref = request.args.get('ref', '')
        designation = request.args.get('designation', '')
        price_min = request.args.get('price_min', type=float)
        price_max = request.args.get('price_max', type=float)
        brand = request.args.get('brand', '')
        stock = request.args.get('stock', '')
        company = request.args.get('company', '')
        category = request.args.get('category', '')
        subcategory = request.args.get('subcategory', '')
        modification_date_min = request.args.get('modification_date_min', '')
        modification_date_max = request.args.get('modification_date_max', '')
        sort_by = request.args.get('sort_by', 'dateajout')
        order = request.args.get('order', 'asc')
        page = request.args.get('page', 1, type=int)
        products_per_page = request.args.get('products_per_page', 10, type=int)

        # Build query filter
        query = {}

        # Modification date filter - default to last 2 days if not specified
        modification_query = {}
        if modification_date_min or modification_date_max:
            try:
                if modification_date_min:
                    min_date = datetime.fromisoformat(modification_date_min.replace('Z', '+00:00'))
                    min_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    modification_query['$gte'] = min_date
                if modification_date_max:
                    max_date = datetime.fromisoformat(modification_date_max.replace('Z', '+00:00'))
                    max_date = max_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    modification_query['$lte'] = max_date
                query['Modifications.dateModification'] = modification_query
            except ValueError:
                return jsonify({'error': 'Invalid date format for modification dates'}), 400
        else:
            # Default: last 2 days
            two_days_ago = datetime.now() - timedelta(days=2)
            query['Modifications.dateModification'] = {'$gte': two_days_ago}

        # Text filters
        if ref:
            query['Ref'] = {'$regex': ref, '$options': 'i'}
        if designation:
            query['Designation'] = {'$regex': designation, '$options': 'i'}
        if brand:
            query['Brand'] = {'$regex': brand, '$options': 'i'}
        if stock:
            query['Stock'] = {'$regex': stock, '$options': 'i'}
        if company:
            query['Company'] = {'$regex': company, '$options': 'i'}
        if category:
            query['Category'] = {'$regex': category, '$options': 'i'}
        if subcategory:
            query['Subcategory'] = {'$regex': subcategory, '$options': 'i'}

        # Price filters
        if price_min is not None or price_max is not None:
            query['Price'] = {}
            if price_min is not None:
                query['Price']['$gte'] = price_min
            if price_max is not None:
                query['Price']['$lte'] = price_max

        # Sorting
        sort_field = sort_by if sort_by in ['price', 'dateajout', 'last_modification'] else 'dateajout'
        sort_field_map = {
            'price': 'Price',
            'dateajout': 'DateAjout',
            'last_modification': 'Modifications.dateModification'
        }
        sort_direction = 1 if order == 'asc' else -1

        # Calculate pagination
        skip = (page - 1) * products_per_page

        # Get total count
        total_products = products_collection.count_documents(query)
        total_pages = (total_products + products_per_page - 1) // products_per_page

        # Fetch products
        products = list(
            products_collection.find(query)
            .sort(sort_field_map[sort_field], sort_direction)
            .skip(skip)
            .limit(products_per_page)
        )

        # Convert ObjectId to string
        for product in products:
            product['_id'] = str(product['_id'])

        # Get stock status counts for modified products
        in_stock_count = products_collection.count_documents({
            **query,
            'Stock': {'$regex': '^in stock$', '$options': 'i'}
        })
        on_order_count = products_collection.count_documents({
            **query,
            'Stock': {'$regex': '^on order$', '$options': 'i'}
        })
        out_of_stock_count = products_collection.count_documents({
            **query,
            'Stock': {'$regex': '^out of stock$', '$options': 'i'}
        })

        response_data = {
            'total_products': total_products,
            'total_pages': total_pages,
            'current_page': page,
            'products_per_page': products_per_page,
            'stock_status': {
                'in_stock': in_stock_count,
                'on_order': on_order_count,
                'out_of_stock': out_of_stock_count
            },
            'products': products
        }

        connection_logger.info(f"Successfully retrieved {len(products)} modified products")

        response = make_response(jsonify(response_data), 200)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        error_logger.error(f"Error in /products/modified endpoint: {str(e)}")
        error_logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# ==================== /products/stats Endpoint ====================
@app.route('/products/stats', methods=['GET'])
def products_stats():
    """
    Returns summary statistics about products:
    - Total products count
    - Total new products (added in last 24 hours)
    - Total modified products (modified in last 2 days)
    - Stock status counts (in stock, on order, out of stock) for:
      * All products
      * New products
      * Modified products
    """
    try:
        connection_logger.info(f"Accessed /products/stats endpoint")

        # Get total products count
        total_products = products_collection.count_documents({})

        # Get new products count (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        total_new_products = products_collection.count_documents({
            'DateAjout': {'$gte': yesterday}
        })

        # Get modified products count (last 2 days)
        two_days_ago = datetime.now() - timedelta(days=2)
        total_modified_products = products_collection.count_documents({
            'Modifications.dateModification': {'$gte': two_days_ago}
        })

        # Get stock status counts for all products
        total_in_stock = products_collection.count_documents({
            'Stock': {'$regex': '^in stock$', '$options': 'i'}
        })
        total_on_order = products_collection.count_documents({
            'Stock': {'$regex': '^on order$', '$options': 'i'}
        })
        total_out_of_stock = products_collection.count_documents({
            'Stock': {'$regex': '^out of stock$', '$options': 'i'}
        })

        # Get stock status counts for new products
        new_in_stock = products_collection.count_documents({
            'DateAjout': {'$gte': yesterday},
            'Stock': {'$regex': '^in stock$', '$options': 'i'}
        })
        new_on_order = products_collection.count_documents({
            'DateAjout': {'$gte': yesterday},
            'Stock': {'$regex': '^on order$', '$options': 'i'}
        })
        new_out_of_stock = products_collection.count_documents({
            'DateAjout': {'$gte': yesterday},
            'Stock': {'$regex': '^out of stock$', '$options': 'i'}
        })

        # Get stock status counts for modified products
        modified_in_stock = products_collection.count_documents({
            'Modifications.dateModification': {'$gte': two_days_ago},
            'Stock': {'$regex': '^in stock$', '$options': 'i'}
        })
        modified_on_order = products_collection.count_documents({
            'Modifications.dateModification': {'$gte': two_days_ago},
            'Stock': {'$regex': '^on order$', '$options': 'i'}
        })
        modified_out_of_stock = products_collection.count_documents({
            'Modifications.dateModification': {'$gte': two_days_ago},
            'Stock': {'$regex': '^out of stock$', '$options': 'i'}
        })

        response_data = {
            'total_products': total_products,
            'total_new_products': total_new_products,
            'total_modified_products': total_modified_products,
            'total_stock_status': {
                'in_stock': total_in_stock,
                'on_order': total_on_order,
                'out_of_stock': total_out_of_stock
            },
            'new_products_stock_status': {
                'in_stock': new_in_stock,
                'on_order': new_on_order,
                'out_of_stock': new_out_of_stock
            },
            'modified_products_stock_status': {
                'in_stock': modified_in_stock,
                'on_order': modified_on_order,
                'out_of_stock': modified_out_of_stock
            }
        }

        connection_logger.info(f"Successfully retrieved product stats")

        response = make_response(jsonify(response_data), 200)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        error_logger.error(f"Error in /products/stats endpoint: {str(e)}")
        error_logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# ==================== /stats Endpoint ====================
@app.route('/stats', methods=['GET'])
def stats():
    """
    Provides statistical data about products, including:
    - Top 10 products with the most modifications
    - Product distribution by category
    - Number of modified products per day in the last month
    - Number of new products added per day in the last month
    """
    try:
        connection_logger.info(f"Accessed /stats endpoint with params: {request.args}")

        stats_type = request.args.get('type', '')

        if not stats_type:
            return jsonify({'error': 'Invalid stats type'}), 400

        # Top 10 products with most modifications
        if stats_type == 'top_modified_products':
            pipeline = [
                {
                    '$project': {
                        'Designation': 1,
                        'modifications_count': {'$size': {'$ifNull': ['$Modifications', []]}}
                    }
                },
                {'$sort': {'modifications_count': -1}},
                {'$limit': 10}
            ]

            result = list(products_collection.aggregate(pipeline))

            # Convert ObjectId to string
            for item in result:
                item['_id'] = str(item['_id'])

            response_data = {'top_modified_products': result}

        # Product distribution by category
        elif stats_type == 'category_distribution':
            pipeline = [
                {
                    '$group': {
                        '_id': '$Category',
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'count': -1}}
            ]

            result = list(products_collection.aggregate(pipeline))
            response_data = {'category_distribution': result}

        # Modified products per day in the last 30 days
        elif stats_type == 'modified_per_day':
            thirty_days_ago = datetime.now() - timedelta(days=30)

            pipeline = [
                {'$unwind': '$Modifications'},
                {
                    '$match': {
                        'Modifications.dateModification': {'$gte': thirty_days_ago}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$Modifications.dateModification'
                            }
                        },
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'_id': 1}}
            ]

            result = list(products_collection.aggregate(pipeline))
            response_data = {'modified_per_day': result}

        # New products added per day in the last 30 days
        elif stats_type == 'added_per_day':
            thirty_days_ago = datetime.now() - timedelta(days=30)

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
            response_data = {'added_per_day': result}

        else:
            return jsonify({'error': 'Invalid stats type'}), 400

        connection_logger.info(f"Successfully retrieved stats for type: {stats_type}")

        response = make_response(jsonify(response_data), 200)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        error_logger.error(f"Error in /stats endpoint: {str(e)}")
        error_logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# ==================== Run Application ====================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
