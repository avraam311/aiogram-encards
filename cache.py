import redis
import json


class Cache:
    def __init__(self, username: str, password: str, host: str, port: int, db: int):
        self.r = redis.Redis(username=username, password=password,
                             host=host, port=port, db=db,
                             decode_responses=True)

    def set_categories_list(self, categories_list):
        serialized_list = json.dumps(categories_list)
        self.r.set('categories', serialized_list)

    def get_categories_list(self):
        serialized_list = self.r.get('categories')
        if serialized_list is None:
            return
        deserialized_list = json.loads(serialized_list)
        return deserialized_list

    def set_sub_categories_list_user(self, sub_categories_list: list, category_id: str):
        serialized_dict = json.dumps(sub_categories_list)
        self.r.set('sub_categories_'+str(category_id), serialized_dict, ex=2592000)

    def delete_sub_category_user(self, sub_category_id: str):
        prefix = 'sub_categories_'+sub_category_id
        self.r.delete(prefix)

    def get_sub_categories_list_user(self, category_id):
        serialized_list = self.r.get('sub_categories_'+str(category_id))
        if serialized_list is None:
            return
        deserialized_list = json.loads(serialized_list)
        return deserialized_list

    def set_sub_categories_list_admin(self, sub_categories_list):
        serialized_list = json.dumps(sub_categories_list)
        self.r.set('sub_categories', serialized_list, ex=2592000)

    def get_sub_categories_list_admin(self):
        serialized_list = self.r.get('sub_categories')
        if serialized_list is None:
            return
        deserialized_list = json.loads(serialized_list)
        return deserialized_list

    def set_banner(self, menu_name: str, banner: str):
        self.r.set(menu_name, banner)

    def get_banner(self, menu_name: str):
        pre_banner = self.r.get(menu_name)
        if pre_banner is None:
            return
        pre_banner = pre_banner.split('banner')

        class Banner:
            pass
        banner = Banner()
        banner.image = pre_banner[0]
        banner.description = pre_banner[1]
        return banner
