import json
from time import time
import tempfile
import os


__all__ = ['parse']


temp_dir = tempfile.gettempdir()
LAUNCH_DATA_FILE = os.path.join(temp_dir, './launch_data.json')

with open(LAUNCH_DATA_FILE, 'w') as file:
    file.write(r'{"launchUuid": ""}')

def timestamp():
    return str(int(time() * 1000))

class Data:
    endpoint = ''
    launch_name = ''
    api_key = ''
    project = ''
    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    base_item_data = {
       'name': 'My Test Suite',
       'type': 'suite',
       'start_time': timestamp(),
       'launchUuid': ''
    }

    @classmethod
    def update_url(cls):
        cls.endpoint = f'{cls.endpoint}/api/v1/{cls.project}'
        cls.update_headers()

    @classmethod
    def update_headers(cls):
        cls.headers = {
            'Authorization': f'Bearer {cls.api_key}'}

    @classmethod
    def read_data_file(cls):
        with open(LAUNCH_DATA_FILE, 'r') as file:
            saved_uuid = os.environ.get('RPORTAL_LAUNCH_UUID')
            if saved_uuid == '':
                data = json.load(file)
                cls.base_item_data['launchUuid'] = data['launchUuid']
            else:
                cls.base_item_data['launchUuid'] = saved_uuid

    @classmethod
    def update_data_file(cls, new_uuid):
        cls.read_data_file()
        cls.base_item_data['launchUuid'] = new_uuid
        os.environ['RPORTAL_LAUNCH_UUID'] = new_uuid
        with open(LAUNCH_DATA_FILE, 'w') as file:
            json.dump(cls.base_item_data, file)
  
def parse():
    Data.endpoint = os.environ.get('RPORTAL_ENDPOINT')
    Data.api_key = os.environ.get('RPORTAL_API_KEY')
    Data.launch_name = os.environ.get('RPORTAL_LAUNCH_NAME')
    Data.project = os.environ.get('RPORTAL_PROJECT')
    Data.update_url()

