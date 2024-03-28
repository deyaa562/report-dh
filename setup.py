from setuptools import setup, find_packages

setup(
    name='rportal',
    version='1.0.0',
    packages=find_packages(),
    entry_points={
        'pytest11': [
            'report=report.plugin'
        ],
        'console_scripts': [
            'rportal=report._config:config'
        ]
    },
    install_requires=[
        'requests',
        'pytest<=7.4.0',
        'decorator'
    ],
    description='Report Portal API',
    long_description='Report Portal API Wrapper',
    license='',
    author='Deyaa Hojerat',
    author_email='deyaah8@d-fendsolutions.com',
    url='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Framework :: Pytest'
    ],
    addopts='-p report'
)