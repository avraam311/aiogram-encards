import redis
import json

from database.models import Category


class Cache:
    def __init__(self, host: str, port: int, db: int):
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def set_categories_list(self, categories_list):
        serialized_list = json.dumps(categories_list)
        self.r.set('categories', serialized_list, ex=2592000)

    def get_categories_list(self):
        serialized_list = self.r.get('categories')
        if serialized_list is None:
            return
        deserialized_list = json.loads(serialized_list)
        return deserialized_list

    def set_sub_categories_list_user(self, sub_categories_list, category_id):
        serialized_dict = json.dumps(sub_categories_list)
        self.r.set('sub_categories_'+str(category_id), serialized_dict, ex=86400)

    def get_sub_categories_list_user(self, category_id):
        serialized_list = self.r.get('sub_categories_'+str(category_id))
        if serialized_list is None:
            return
        deserialized_list = json.loads(serialized_list)
        return deserialized_list

    def set_sub_categories_list_admin(self, sub_categories_list):
        serialized_list = json.dumps(sub_categories_list)
        self.r.set('sub_categories', serialized_list, ex=86400)

    def get_sub_categories_list_admin(self):
        serialized_list = self.r.get('sub_categories')
        if serialized_list is None:
            return
        deserialized_list = json.loads(serialized_list)
        return deserialized_list

    def set_items_list(self, items_list, sub_category_id):
        serialized_list = json.dumps(items_list)
        self.r.set('items_'+str(sub_category_id), serialized_list, ex=86400)

    def get_items_list(self, sub_category_id):
        serialized_list = self.r.get('items_'+str(sub_category_id))
        if serialized_list is None:
            return
        deserialized_list = json.loads(serialized_list)
        return deserialized_list
