from typing import Dict, List, Optional, Union
import requests
import json
import os
import inspect
import json
from ._data import timestamp, Data, parse
import tempfile
import contextvars
from collections import OrderedDict


__all__ = ['Launch']
temp_dir = tempfile.gettempdir()
FILE_PATH = os.path.join(temp_dir, 'rportal.json')


def add_temp_file():
    with open(FILE_PATH, 'w') as file:
        file.write(r'{"": ""}')


class Launch:
    _instance = None
    caller_name_var = contextvars.ContextVar('caller_name', default='')
    available_items = OrderedDict()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def items(cls) -> dict:
        launch_id = cls.get_launch_id()
        response = requests.get(
            url=f'{Data.endpoint}/item',
            headers=Data.headers,
            params={
                'filter.eq.launchId': launch_id,
                'isLatest': True,
                'launchesLimit': 1})

        response_json = response.json()
        return response_json['content']

    @classmethod
    def add_item(cls, item_name: str, item_uuid: str, description: str = ''):
        cls.available_items[item_name] = {'uuid': item_uuid, 'description': description}
        with open(FILE_PATH, 'w') as file:
            json.dump(cls.available_items, file, indent=4)

    @classmethod
    def get_latest_item(cls, local: bool = True):
        if local:
            try:
                last_key = next(reversed(cls.available_items))
                return cls.available_items[last_key]
            except (KeyError, StopIteration):
                pass

        launch_id = cls.get_launch_id()
        response = requests.get(
            url=f'{Data.endpoint}/item',
            headers=Data.headers,
            params={
                'filter.eq.launchId': launch_id,
                'isLatest': True,
                'launchesLimit': 1,
                'page.size': 1})

        response_json = response.json()
        item_page = response_json['page']
        pages_number = item_page['totalPages']
        response = requests.get(
            url=f'{Data.endpoint}/item',
            headers=Data.headers,
            params={
                'filter.eq.launchId': launch_id,
                'isLatest': True,
                'launchesLimit': 1,
                'page.size': 1,
                'page.page': pages_number})
        
        response_json = response.json()
        return response_json['content'][0]

    @classmethod
    def get_item_by_attribute(cls, attribute: str, local: bool = True):
        if attribute == '':
            return ''

        if local:
            try:
                return cls.available_items[attribute]
            except KeyError:
                pass

        launch_id = cls.get_launch_id()
        response = requests.get(
            url=f'{Data.endpoint}/item',
            headers=Data.headers,
            params={
                'filter.eq.launchId': launch_id,
                'filter.eq.value': attribute})
        
        response_json = response.json()
        try:
            return response_json['content'][-1]
        except:
            return ''


    @classmethod
    def get_item_by_name(cls, name: str, local: bool = True):
        if name == '':
            return ''

        if local:
            try:
                return cls.available_items[name]
            except KeyError:
                pass

        launch_id = cls.get_launch_id()
        response = requests.get(
            url=f'{Data.endpoint}/item',
            headers=Data.headers,
            params={
                'filter.eq.launchId': launch_id,
                'filter.eq.name': name})
        
        response_json = response.json()
        try:
            return response_json['content'][-1]
        except:
            return []
    @classmethod
    def get_in_progress_item_by_name(cls, name: str):
        if name == '':
            return ''
        launch_id = cls.get_launch_id()
        response = requests.get(
            url=f'{Data.endpoint}/item',
            headers=Data.headers,
            params={
                'filter.eq.launchId': launch_id,
                'filter.eq.value': name,
                'filter.eq.status': 'IN_PROGRESS'})
        
        response_json = response.json()
        try:
            return response_json['content'][-1]
        except:
            return []

    @classmethod
    def get_caller_name(cls):
        return cls.caller_name_var.get()


    @classmethod
    def start_launch(cls):
        data = {
            'name': Data.launch_name,
            f'startTime': timestamp()}

        add_temp_file()
        Data.read_data_file()
        rportal_launch_uuid = os.environ['RPORTAL_LAUNCH_UUID']
        if rportal_launch_uuid == '' or rportal_launch_uuid is None:
            try:
                respone = requests.post(url=f'{Data.endpoint}/launch', headers=Data.headers, json=data)
                launch_uuid = respone.json()['id']
                Data.update_data_file(launch_uuid)
            except:
                pass

    @classmethod
    def finish_launch(cls):
        requests.put(url=f'{Data.endpoint}/launch/{Data.base_item_data["launchUuid"]}/finish', headers=Data.headers, json={'endTime': timestamp()})


    @classmethod
    def get_launch_id(cls):
        response = requests.get(
                url=f'{Data.endpoint}/launch/latest',
                headers=Data.headers,
                params={'filter.eq.uuid': f'{os.environ.get("RPORTAL_LAUNCH_UUID")}'})

        response_launch = response.json()
        try:
            response_content = response_launch['content'][-1]
            launch_id = response_content['id']
            return launch_id

        except KeyError:
            return None

    @classmethod
    def get_launch_data(cls):
        launch_id = cls.get_launch_id()
        response = requests.get(
            url=f'{Data.endpoint}/launch/{launch_id}',
            headers=Data.headers)
        
        return response.json()

    @classmethod
    def update_launch(cls, description: str, attributes: dict = {}):
        launch_data = cls.get_launch_data()
        launch_id = launch_data['id']
        current_attributes = launch_data['attributes']
        try:
            current_description = launch_data['description']

        except KeyError:
            current_description = ''

        new_description = '\n'.join([current_description, description])

        for key, value in attributes.items():
            current_attributes.append({"key": key, "value": value})

        json_data = {
            "attributes": current_attributes,
            "description": new_description,
            "mode": "DEFAULT"
        }
        response = requests.put(
            url=f'{Data.endpoint}/launch/{launch_id}/update',
            headers=Data.headers,
            json=json_data)
        
        return response.json()

    @classmethod
    def update_item(cls, item_name: Optional[str] = None, description: str = '', attributes: dict = {}, params: List[dict] = []):
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            try:
                item = cls.get_item_by_attribute(item_name, local=False)
                try:
                    current_attributes = item['attributes']
                
                except KeyError:
                    current_attributes = []

                try:
                    current_description = item['description']
        
                except KeyError:
                    current_description = ''
        
                new_description = '\n'.join([current_description, description])
                for key, value in attributes.items():
                    current_attributes.append({"key": key, "value": value})

                try:
                    current_params = item['parameters']
                    new_params = current_params + params
                except KeyError:
                    new_params = params

                json_data= {
                    'launchUuid': os.environ['RPORTAL_LAUNCH_UUID'],
                    'description': new_description,
                    'attributes': current_attributes,
                    'parameters': new_params}

                data = Data.headers.copy()
                data['Content-Type']='application/json'
                requests.put(url=f'{Data.endpoint}/item/{item["id"]}/update', headers=data, json=json_data)
                requests.put(url=f'{Data.endpoint}/item/{item["id"]}/update', headers=data, json=json_data)
                pass
            except:
                pass

    @classmethod
    def get_all_available_items(cls):
        launch_id = cls.get_launch_id()
        if launch_id is not None:
            response = requests.get(
                    url=f'{Data.endpoint}/item',
                    headers=Data.headers,
                    params={
                        'filter.eq.launchId': launch_id,
                        'isLatest': True,
                        'launchesLimit': 1
                    })
            return response.json()['content']

        return {}

    @classmethod
    def create_report_item(
            cls,
            name: str,
            parent_item: str = '',
            parent_uuid: Optional[str] = None,
            type: str = '',
            attributes: List[str] = [],
            description: str = '',
            has_stats: bool = True,
            parameters: List[dict] = []):

        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            parent_data = cls.get_item_by_attribute(parent_item)
            try:
                parent_uuid = parent_uuid if parent_uuid is not None else parent_data['uuid']
            
            except TypeError:
                parent_uuid = ''

            if os.environ['RPORTAL_LAUNCH_UUID'] != '':
                Data.read_data_file()

            data = Data.base_item_data
            data['name'] = name
            data['type'] = type
            data['start_time'] = timestamp()
            data['description'] = description
            data['hasStats'] = has_stats
            data['attributes'] = attributes
            data['parameters'] = parameters

            response = requests.post(url=f'{Data.endpoint}/item/{parent_uuid}', headers=Data.headers, json=data)
            response_json = response.json()
            return response_json['id'] 

    @classmethod
    def finish_item(cls, item_name: str, status: str = ''):
        status = status if len(status) else 'passed'
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            try:
                item = cls.get_item_by_attribute(item_name)
                item_uuid = item['uuid']
                json_data= {
                    'launchUuid': os.environ['RPORTAL_LAUNCH_UUID'],
                    'endTime': timestamp(),
                    'status': status}

                data = Data.headers.copy()
                data['Content-Type']='application/json'
                requests.put(url=f'{Data.endpoint}/item/{item_uuid}', headers=data, json=json_data)

            except Exception as exc:
                pass

            finally:
                if item_name in cls.available_items:
                    del cls.available_items[item_name]


    @classmethod
    def finish_item_by_uuid(cls, item_uuid: str, status: str = ''):
        status = status if len(status) else 'passed'
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            try:
                json_data= {
                    'launchUuid': os.environ['RPORTAL_LAUNCH_UUID'],
                    'endTime': timestamp(),
                    'status': status}

                data = Data.headers.copy()
                data['Content-Type']='application/json'
                response = requests.put(url=f'{Data.endpoint}/item/{item_uuid}', headers=data, json=json_data)
                response = requests.put(url=f'{Data.endpoint}/item/{item_uuid}', headers=data, json=json_data)
            except:
                pass


    @classmethod
    def finish_skipped_item(cls, item_name: str, reason: Optional[str] = None):
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            try:
                item = cls.get_item_by_attribute(item_name)
                item_uuid = item['uuid']
                json_data= {
                'launchUuid': os.environ['RPORTAL_LAUNCH_UUID'],
                'endTime': timestamp(),
                'status': 'skipped',
                'issue': {
                    'issueType': 'nd001',
                    'comment': reason},
                'description': reason}

                data = Data.headers.copy()
                data['Content-Type']='application/json'
                requests.put(url=f'{Data.endpoint}/item/{item_uuid}', headers=data, json=json_data)
            except:
                pass

    @classmethod
    def finish_failed_item(cls, item_name: str, message: str, issueType: str = 'pb001'):
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            item = cls.get_item_by_attribute(item_name)
            item_uuid = item['uuid']
            json_data = {
                'launchUuid': os.environ['RPORTAL_LAUNCH_UUID'],
                'endTime': timestamp(),
                'status': 'failed',
                'issue': {
                    'issueType': issueType,
                    'comment': message}}

            requests.put(url=f'{Data.endpoint}/item/{item_uuid}', headers=Data.headers, json=json_data)
            requests.put(url=f'{Data.endpoint}/item/{item_uuid}', headers=Data.headers, json=json_data)

    @classmethod
    def finish_failed_item_by_uuid(cls, item_uuid: str, message: str):
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            json_data = {
                'launchUuid': os.environ['RPORTAL_LAUNCH_UUID'],
                'endTime': timestamp(),
                'status': 'failed',
                'issue': {
                    'issueType': 'pb001',
                    'comment': message}}

            requests.put(url=f'{Data.endpoint}/item/{item_uuid}', headers=Data.headers, json=json_data)
            requests.put(url=f'{Data.endpoint}/item/{item_uuid}', headers=Data.headers, json=json_data)

    @classmethod
    def create_log(cls, item: str, message: str, level: str = "INFO"):
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            required_item = cls.get_item_by_attribute(item)
            item_uuid = required_item['uuid']
            json_data = {
                "launchUuid": os.environ['RPORTAL_LAUNCH_UUID'],
                "itemUuid": item_uuid,
                "time": timestamp(),
                "message": message,
                "level": level,
            }

            response = requests.post(url=f'{Data.endpoint}/log/entry', headers=Data.headers, json=json_data)
            return response.json()
    
    @classmethod
    def log_error(cls, parent_item: str, header: str, message: str):
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            required_item = cls.get_item_by_attribute(parent_item, local=True)
            if len(required_item) <= 0:
                item = Launch.get_latest_item(local=True)
                item = Launch.get_item_by_uuid(item['uuid'])
                item_uuid = item['uuid']

            else:
                item_uuid = required_item['uuid']
            parent_uuid = cls.create_report_item(
                name=f'**{header}**',
                parent_uuid=item_uuid,
                type='step',
                has_stats=False,
                description='',
                attributes=[{'key': 'name', 'value': getattr(required_item, 'name', 'name')}],
                parameters=[{'key': 'name', 'value': getattr(required_item, 'name', 'name')}])

            json_data = {
                "launchUuid": os.environ['RPORTAL_LAUNCH_UUID'],
                "itemUuid": parent_uuid,
                "time": timestamp(),
                "message": message,
                "level": "fatal",
            }

            response = requests.post(url=f'{Data.endpoint}/log', headers=Data.headers, json=json_data)
            cls.finish_item_by_uuid(parent_uuid, 'failed')
            return response.json()

    @classmethod
    def add_attachment_entry(cls, message: str, level: str, item: str = ''):
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            file_name = message
            latest_item = cls.get_latest_item()
            item_uuid = cls.get_item_by_attribute(item)['uuid'] if len(item) > 0 else latest_item['uuid']
            json_data = {
                "file": {
                  "name": file_name
                },
                "itemUuid": item_uuid,
                "launchUuid": os.environ['RPORTAL_LAUNCH_UUID'],
                "level": level,
                "message": message,
                "time": timestamp()}
            response = requests.post(url=f'{Data.endpoint}/log/entry', headers=Data.headers, json=json_data)
            response_json = response.json()
            return response_json['id']

    @classmethod
    def add_attachment(cls, message: str, level: str, attachment: Union[str, bytes], attachment_type: str, item: str = ''):
        if os.environ['RPORTAL_LAUNCH_UUID'] != '':
            file_name = message # if type(attachment) == bytes else os.path.basename(attachment)
            latest_item = cls.get_latest_item()
            item_uuid = cls.get_item_by_attribute(item)['uuid'] if len(item) > 0 else latest_item['uuid']
            json_body = {
                "launchUuid": os.environ['RPORTAL_LAUNCH_UUID'],
                "time": timestamp(),
                "message": message,
                "level": level,
                "itemUuid": item_uuid,
                "file": {"name": file_name}}

            data = b''
            data += b'--boundary-string\r\n'
            data += f'Content-Disposition: form-data; name="json_request_part"\r\n'.encode('utf-8')
            data += b'Content-Type: application/json\r\n\r\n'
            data += json.dumps([json_body]).encode('utf-8')
            data += b'\r\n--boundary-string\r\n'
            data += f'Content-Disposition: form-data; name="{file_name}"; filename="{file_name}"\r\n'.encode('utf-8')
            data += f'Content-Type: {attachment_type}\r\n\r\n'.encode('utf-8')
            file_data = read_file_data(attachment)
            data += file_data
            data += b'\r\n--boundary-string--\r\n'
            headers = Data.headers.copy()
            headers['Content-Type'] = 'multipart/form-data; boundary=boundary-string'
            response = requests.post(url=f'{Data.endpoint}/log', headers=headers, data=data)
            response_json = response.json()
            return response_json['responses'][0]['id']


    @classmethod
    def get_item_by_uuid(cls, uuid: str):
        launch_id = cls.get_launch_id()
        response = requests.get(
            url=f'{Data.endpoint}/item',
            headers=Data.headers,
            params={
                'filter.eq.launchId': launch_id,
                'filter.eq.uuid': uuid})
        
        response_json = response.json()
        try:
            return response_json['content'][0]
        except:
            return {}

def read_file_data(file: Union[str, bytes]):
        if type(file) == bytes:
            return file
        else:
            try:
                with open(file, 'rb') as f:
                    return f.read()
            except OSError:
                return bytes(file, 'utf-8')



def is_item_available(available_items: List[dict], item_name: str):
    if item_name != '':
        for item in available_items:
            if item_name == item['name']:
                pass
                return True

        return False        