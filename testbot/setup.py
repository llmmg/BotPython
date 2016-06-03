"""document test setup"""

from setuptools import setup, find_packages

setup(
    name='votebot',

    version='1.0',
    description=__doc__,
    packages=find_packages(),

    install_requires=('aiohttp', 'json', 'asyncio'),
    extra_requires={
        'doc': ('Sphinx', 'sphinx_rtd_theme'),
    }
)

repr(find_packages)
