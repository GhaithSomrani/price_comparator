import pymongo
from itemadapter import ItemAdapter
from datetime import datetime

class TunisianetPipeline:
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["product_comparator"]
        self.collection = self.db["data_product"]

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
        self.collection.insert_one(data)


class MytekPipline:
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["product_comparator"]
        self.collection = self.db["data_product"]

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
        self.collection.insert_one(data)