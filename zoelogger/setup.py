from setuptools import find_packages, setup

setup(
    name="zoelogger",
    version="0.2.5.dev0",
    packages=find_packages(),
    install_requires=[
        "loguru~=0.6.0",
        "better-exceptions~=0.3.3",
        "python-dateutil~=2.8.1",
        "pytest-asyncio",
    ],
)
