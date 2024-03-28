import argparse
from .src import _internal


__all__ = 'config',


def config():
    parser = argparse.ArgumentParser(description='Pytest Report Portal Wrapper')
    parser.add_argument('--host', '-H', default='localhost', help='host:ip or domain name (Example: localhost:8080)')
    parser.add_argument('--launch-name', '-l', default='new launch' ,help='New launch name ( default is "new launch" )')
    parser.add_argument('--api-key', '-u', required=True, help='API Key access token')
    parser.add_argument('--project-name', '-p', required=True, help='Report Portal project name')
    args = parser.parse_args()
    print(args.bearer_uuid)
    _internal.Data.endpoint = args.host
    _internal.Data.launch_name = args.launch_name
    _internal.Data.api_key = args.bearer_uuid
    _internal.Data.project = args.project_name
    _internal.Data.update_url()
    _internal.Data.update_headers()


if __name__ == '__main__':
    data = config()

