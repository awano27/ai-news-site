from setuptools import setup, find_packages

setup(
    name='ai-news-site',
    version='0.1.0',
    packages=[
        'scripts',
        'scripts.collectors',
        'src',
        'src.auto_collect',
        'src.auto_collect.collectors',
        'src.generators',
        'src.utils',
    ],
)
