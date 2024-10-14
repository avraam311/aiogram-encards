import redis
import json


class Cache:
    def __init__(self, host: str, port: int, db: int):
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def set_items_list(self, sub_category, items_list):
        new_items_list = []
        for item in items_list:

            item_id = item.id
            item_media = item.item_media
            media_text = item.media_text
            
            new_items_list.append([item_id, item_media, media_text])

        serialized_list = json.dumps(new_items_list)
        print(serialized_list)
        self.r.set(sub_category, serialized_list, ex=86400)

    def get_items_list(self, sub_category):
        serialized_list = self.r.get(sub_category)
        if serialized_list is None:
            return
        deserialized_list = json.loads(serialized_list)
        return deserialized_list
