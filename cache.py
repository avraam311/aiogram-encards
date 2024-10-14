import redis
import json


class Cache:
    def __init__(self, host: str, port: int, db: int):
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def set_items_list(self, sub_category, items_list):
        items_dict = dict()
        for media in items_list:

            item_media = media.item_media
            media_text = media.media_text

            items_dict[item_media] = media_text

        serialized_dict = json.dumps(items_dict)
        print(serialized_dict)
        self.r.set(sub_category, serialized_dict, ex=86400)

    def get_items_dict(self, sub_category):
        items_dict = self.r.get(sub_category)
        if items_dict:
            deserialized_dict = json.loads(items_dict)
            return deserialized_dict
