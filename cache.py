import redis
import json


class Cache:
    def __init__(self, host: str, port: int, db: int):
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def set_categories_list(self, categories_list):
        categories_dict = {}

        for category in categories_list:
            categories_dict[category.id] = category.name

        serialized_dict = json.dumps(categories_dict)
        self.r.set('categories', serialized_dict, ex=2592000)

    def get_categories_dict(self):
        serialized_dict = self.r.get('categories')
        if serialized_dict is None:
            return
        deserialized_dict = json.loads(serialized_dict)
        return deserialized_dict

    def set_sub_categories_list_admin(self, sub_categories_list):
        sub_categories_dict = {}

        for sub_category in sub_categories_list:
            sub_categories_dict[sub_category.id] = sub_category.name

        serialized_dict = json.dumps(sub_categories_dict)
        self.r.set('sub_categories', serialized_dict, ex=86400)

    def get_sub_categories_dict_admin(self):
        serialized_dict = self.r.get('sub_categories')
        if serialized_dict is None:
            return
        deserialized_dict = json.loads(serialized_dict)
        return deserialized_dict

    def set_items_list(self, sub_category, items_list):
        new_items_list = []
        for item in items_list:

            item_id = item.id
            item_media = item.item_media
            media_text = item.media_text
            
            new_items_list.append([item_id, item_media, media_text])

        serialized_list = json.dumps(new_items_list)
        self.r.set(sub_category, serialized_list, ex=86400)

    def get_items_list(self, sub_category):
        serialized_list = self.r.get(sub_category)
        if serialized_list is None:
            return
        deserialized_list = json.loads(serialized_list)
        return deserialized_list
