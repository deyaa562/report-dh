from typing import Tuple
import pytest
from .src._data import parse
from .src._internal import Launch
from .src.core import *

import asyncio
import os


def is_tests_path(config):
    testpaths = config.getoption("file_or_dir")
    return any(p == './tests' for p in testpaths)


def prettify_item_name(item_name: str):
    new_item_name = item_name
    new_item_name = new_item_name.replace('-', ' ')
    new_item_name = new_item_name.replace('[', ' ')
    new_item_name = new_item_name.replace(']', '')
    parts = ' '.join(new_item_name.split('_'))
    parts = parts.split(' ')
    new_item_name = [part.capitalize() for part in parts]
    new_item_name = ' '.join(new_item_name)
    return new_item_name


def add_fixtures_to_teardown(fixture_name, teardown_name):
    item_uuid = Launch.create_report_item(
            name=f'**{fixture_name}**',
            parent_item=teardown_name,
            type='step',
            description='',
            has_stats=False,
            parameters=[{'key': 'name', 'value': fixture_name}])

    Launch.add_item(fixture_name, item_uuid)

def pytest_addoption(parser):
    parser.addoption("--report", action="store_true", default=False)


def pytest_configure(config):
    """
    Registers the required flags that are used by our plugin
    """
    config.addinivalue_line("markers", "feature()")
    config.addinivalue_line("markers", "story")
    if config.getoption("--report") and not is_tests_path(config):
        os.environ['REPORT_FLAG_PASSED'] = 'True'
        parse()


def pytest_collection_finish(session):
    """
    Runs when the pytest collection is finished and before the pytest session starts
    """
    if session.config.getoption("--report") and not is_tests_path(session.config) and not session.config.getoption("--collect-only"):
        Launch.start_launch()


def pytest_sessionfinish(session, exitstatus):
    """
    Runs when the pytest session is finished
    """
    if session.config.getoption("--report") and not is_tests_path(session.config) and not session.config.getoption("--collect-only"):
        # This finishes all tests that are still in progress
        items = Launch.items()
        reversed_items = items[::-1] # We reverse the items list to finish the items from first to last
        if reversed_items is not None:
            for item in reversed_items:
                if item['status'] == 'IN_PROGRESS':
                    Launch.finish_item(item['name'])

        try:
            Launch.finish_launch()
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.close()

        except RuntimeError:
            pass


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    """
    Runs before the test setup is started
    """
    if item.config.getoption("--report") and not is_tests_path(item.config):
        add_test_features_and_stories(item)
        test_name = getattr(item.function, '__new_name__', prettify_item_name(item.name))

        # executes the block of code below in case the test is not yet started and has a parent class
        if item.name not in Launch.items() and item.parent is not None:
            attributes = get_test_attributes(item)
            params_list = get_test_params(item)
            parent_item = Launch.get_item_by_attribute(item.parent.name)
            parent_uuid = parent_item['uuid'] if len(parent_item) else ''
            item_id = Launch.create_report_item(
                name=test_name,
                parent_uuid=parent_uuid,
                type='test',
                has_stats=True,
                description='',
                attributes=attributes,
                parameters=params_list)

            Launch.add_item(item.name.split(' ')[0], item_id)
            item_is_not_skipped = 'skip' not in attributes

            if item_is_not_skipped:
                item_setup_name: str
                item_setup_name = prettify_item_name(item.name)
                item_setup_name = f'{item_setup_name} Setup'
                item_id = Launch.create_report_item(
                    name=item_setup_name,
                    parent_item=item.name,
                    type='before_test',
                    has_stats=True,
                    description='',
                    parameters=[{'key': 'name', 'value': f'{item.name}_Setup'}])

                Launch.add_item(f'{item.name}_{item_setup_name}', item_id)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    """
    Runs before the test teardown
    """
    if item.config.getoption("--report") and not is_tests_path(item.config):
        attributes = [marker.name for marker in item.iter_markers()]
        item_is_not_skipped = 'skip' not in attributes
        if item_is_not_skipped:
            item_teardown_name: str
            item_teardown_name = prettify_item_name(item.name)
            item_teardown_name = f'{item_teardown_name} Teardown'
            item_id = Launch.create_report_item(
                name=item_teardown_name,
                parent_item=item.name,
                type='after_test',
                has_stats=True,
                description='',
                parameters=[{'key': 'name', 'value': f'{item.name}_Teardown'}])

            teardown_name = f'{item.name}_{item_teardown_name}'
            Launch.add_item(teardown_name, item_id)

            # This finishes all the test fixtures
            # request, event_loop and _xunit_setup_class are default pytest fixtures that we need to ignore
            for fixture_name in item.fixturenames:
                if 'request' not in fixture_name and 'event_loop' not in fixture_name:
                    if '_xunit_setup_class' not in fixture_name:
                        add_fixtures_to_teardown(fixture_name, teardown_name)
                        required_fixture = item._fixtureinfo.name2fixturedefs[fixture_name][0]
                        required_fixture.addfinalizer(lambda fixture_name=fixture_name: Launch.finish_item(fixture_name))


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    Runs after each test stage is finished
    """
    if item.config.getoption("--report") and not is_tests_path(item.config):
        excinfo = call.excinfo
        attributes = [marker.name for marker in item.iter_markers()]
        item_is_not_skipped = 'skip' not in attributes
        if item_is_not_skipped:
            if call.when == 'setup': # Runs after the test setup is done
                run_item_teardown(f'{item.name}_Setup', excinfo)

            if call.when == 'call': # Runs after the test body (execution) is done
                run_item_teardown(f'{item.name}_Execution', excinfo)

            if call.when == 'teardown': # Runs after the test teardown is done
                run_item_teardown(f'{item.name}_Teardown', excinfo)

def pytest_report_teststatus(report):
    """
    Runs after the test teardown
    """
    if report.skipped:
        test_name = report.nodeid.split('::')[-1]
        item_name = test_name.split(' ')[0]

        # This runs in case a test is marked as xfail  
        reprcrash = getattr(report.longrepr, 'reprcrash', None)
        if reprcrash: # if test is expected to fail
            if report.when == 'call':
                Launch.log_error(f'{item_name}_Execution', header='STACK TRACE', message=f'XFAIL {report.wasxfail}')
                Launch.finish_failed_item(f'{item_name}_Execution', f'XFAIL {report.wasxfail}', issueType='si001')

        else:
            reason = report.longrepr[-1]
            if report.when == 'setup':
                Launch.finish_skipped_item(item_name, reason)

            if report.when == 'call':
                Launch.finish_skipped_item(f'{item_name}_Execution', reason)
                Launch.finish_skipped_item(item_name, reason)


def pytest_exception_interact(node, call, report):
    """
    Runs in case an exception has occured during any stage of the test
    """
    if node.config.getoption("--report") and not is_tests_path(node.config) and not node.config.getoption("--collect-only"):
        __tracebackhide__ = True
        item_name_to_finish = ''
        if call.when == 'call':
            item_name_to_finish = f'{node.name}_Execution'

        elif call.when == 'setup':
            item_name_to_finish = f'{node.name}_Setup'

        elif call.when == 'teardown':
            item_name_to_finish = f'{node.name}_Teardown'

        excinfo = call.excinfo
        traceback = getattr(report.longrepr, 'reprtraceback', None)
        if traceback:
            last_entry = traceback.reprentries[-1]
            if hasattr(last_entry, 'reprfileloc'):
                # This is for ReprEntry
                formatted_traceback = str(last_entry.reprfileloc)
            else:
                formatted_traceback = str(last_entry)
        else:
            formatted_traceback = ''

        traceback_str = str(formatted_traceback)
        traceback_str = f'{traceback_str}\n\n-------------------------------------------------------------\n\n'
        traceback_str = f'{traceback_str}{report.longreprtext}'
        Launch.log_error(item_name_to_finish, header='STACK TRACE', message=traceback_str)
        # pytest_node_name = os.environ.get('PYTEST_CURRENT_TEST').split('::')[-1]
        last_test_name = _get_current_test_state()
        Launch.finish_failed_item(item_name_to_finish, message=traceback_str)
        Launch.finish_failed_item(last_test_name, message=traceback_str)
        if 'Setup' in item_name_to_finish:
            item_id = add_item_execution(node.name)
            Launch.add_item(f'{node.name}_Execution', item_id)
            Launch.finish_failed_item(node.name, message='Failed on Setup', issueType='ab001')

def run_item_teardown(item_name: str, excinfo):
    """
    Run the teardown of each item (test setup, body or teardown)
    """
    if excinfo is None:
        # start item execution if setup is done
        if 'Setup' in item_name:
            required_item = item_name.split('_Setup')[0]
            item_id = add_item_execution(required_item)
            Launch.add_item(f'{required_item}_Execution', item_id)

        # finish item whether it's setup, execution or teardown
        Launch.finish_item(item_name)

        # finish test "Class" if it's teardown is finished
        if 'Teardown' in item_name:
            required_item = item_name.split('_Teardown')[0]
            Launch.finish_item(required_item)


def add_item_execution(item_name):
    """
    Start the test body
    """
    execution_name = prettify_item_name(item_name)
    return Launch.create_report_item(
        name=f'{execution_name} Body',
        parent_item=item_name,
        type='scenario',
        has_stats=True,
        description='',
        parameters=[{'key': 'name', 'value': f'{item_name}_Execution'}])


def get_formatted_item_name(item):
    item_func = getattr(item.cls, item.name.split('[')[0])
    return getattr(item_func, '__new_name__', item.name)

def add_test_features_and_stories(item):
    available_items = Launch.items()
    markers = item.parent.own_markers.copy()
    filtered_markers = [marker for marker in markers if marker.name in ['story', 'feature']]
    filtered_markers.reverse()
    sorted(filtered_markers, key=lambda p, idx=enumerate(filtered_markers): (0 if p.name == 'feature' else 1, next(idx)[0]))
    for index in range(len(filtered_markers)):
        marker = filtered_markers[index]
        if marker.name in ['feature', 'story']:
            marker_name = marker.kwargs['name']
            marker_class_name = marker.kwargs['class_name']
            parent = filtered_markers[index - 1] if index > 0 else None
            parent_class_name = parent.kwargs['class_name'] if parent else ''
            parent_item = Launch.get_item_by_attribute(parent_class_name) if parent_class_name != '' else ''
            parent_uuid = parent_item['uuid'] if parent_item != '' else None
            # parent_uuid = parent_item['uuid'] if parent_item != '' else None
            type = 'suite' if marker.name == 'feature' else 'story'
            marker_feature_name = Launch.get_item_by_name(marker_name)
            if len(marker_feature_name) == 0:
                item_id = Launch.create_report_item(
                    name=marker_name,
                    parent_item=parent_class_name,
                    parent_uuid=parent_uuid,
                    type=type,
                    attributes=[],
                    description='',
                    has_stats=True,
                    parameters=[{'key': 'name', 'value': f'{marker_class_name}'}])

                Launch.add_item(marker_name, item_id)



def get_test_attributes(item):
    attributes = [marker.name for marker in item.iter_markers()]
    if 'parametrize' in attributes:
        attributes.remove('parametrize')

    attributes = [attr for attr in attributes if attr not in ['story', 'feature', 'parametrize', 'asyncio']]
    return attributes


def get_test_params(item):
    try:
        params = item.callspec.params
        params_list = [{"key": param, "value": str(value)} for param, value in params.items()]

    except:
        params_list = []

    params_list.append({'key': 'name', 'value': item.name})
    return params_list