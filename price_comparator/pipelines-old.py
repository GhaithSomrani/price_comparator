import time
import mysql.connector
from itemadapter import ItemAdapter
from datetime import datetime


class TunisianetPipeline:

    def __init__(self):
        self.create_connection()
        self.create_table()

    def create_connection(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="product_comparator"
        )
        self.curr = self.conn.cursor()

    def create_table(self):
        self.curr.execute("""
            CREATE TABLE IF NOT EXISTS data_product (
                id INT AUTO_INCREMENT PRIMARY KEY,
                store VARCHAR(255),
                reference VARCHAR(255),
                name VARCHAR(255),
                price DECIMAL(10, 2),
                category VARCHAR(255),
                availability VARCHAR(255),
                brand VARCHAR(255),
                url VARCHAR(255),
                imageurl VARCHAR(255),
                add_date TIMESTAMP
            )
        """)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if adapter.get('reference'):
            data = {
                'store': 'tunisianet',
                'reference': adapter["reference"],
                'name': adapter["productname"],
                'price': adapter["price"],
                'category': adapter['category'],
                'availability': adapter['availability'],
                'brand': adapter['brand'],
                'url': adapter['Url'],
                'imageurl': adapter['imageUrl'],
                'add_date': datetime.now(),
            }

            self.store_in_database(data)
        return item

    def store_in_database(self, data):
        self.curr.execute("""
            INSERT INTO data_product (store, reference, name, price, category, availability, brand, url, imageurl, add_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['store'],
            data['reference'],
            data['name'],
            data['price'],
            data['category'],
            data['availability'],
            data['brand'],
            data['url'],
            data['imageurl'],
            data['add_date']
        ))
        self.conn.commit()


class MytekPipline:
    def __init__(self):
        self.create_connection()
        self.create_table()

    def create_connection(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="product_comparator"
        )
        self.curr = self.conn.cursor()

    def create_table(self):
        self.curr.execute("""
            CREATE TABLE IF NOT EXISTS data_product (
                id INT AUTO_INCREMENT PRIMARY KEY,
                store VARCHAR(255),
                reference VARCHAR(255),
                name VARCHAR(255),
                price DECIMAL(10, 2),
                category VARCHAR(255),
                availability VARCHAR(255),
                brand VARCHAR(255),
                url VARCHAR(255),
                imageurl VARCHAR(255),
                add_date TIMESTAMP
            )
        """)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if adapter.get('reference'):
            data = {
                'store': 'mytek',
                'reference': adapter["reference"],
                'name': adapter["productname"],
                'price': adapter["price"],
                'category': adapter['category'],
                'availability': adapter['availability'],
                'brand': adapter['brand'],
                'url': adapter['Url'],
                'imageurl': adapter['imageUrl'],
                'add_date': datetime.now(),
            }

            self.store_in_database(data)
        return item

    def store_in_database(self, data):
        self.curr.execute("""
            INSERT INTO data_product (store, reference, name, price, category, availability, brand, url, imageurl, add_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['store'],
            data['reference'],
            data['name'],
            data['price'],
            data['category'],
            data['availability'],
            data['brand'],
            data['url'],
            data['imageurl'],
            data['add_date']
        ))
        self.conn.commit()
    
