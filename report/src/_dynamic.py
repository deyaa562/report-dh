from ._internal import Launch
import requests
from ._data import Data
from .core import *
import os

__all__ = ['dynamic']



class dynamic:
    @classmethod
    def link(cls, title: str, url: str):
        if not _is_report_flag_enabled():
            return

        new_link = f'[{title}]({url})'
        caller = _get_current_test_state()
        item = Launch.get_item_by_attribute(caller, local=False)
        if len(item) <= 0:
            item = Launch.get_latest_item(local=True)
            item = Launch.get_item_by_uuid(item['uuid'])

        description = item['description']
        new_description = '\n'.join([description, new_link])
        new_data = {'description': new_description}
        response = requests.put(url=f'{Data.endpoint}/item/{item["id"]}/update', headers=Data.headers, json=new_data)
        pass
