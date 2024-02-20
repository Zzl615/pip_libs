from setuptools import find_packages, setup

setup(
    name="zoe_injector_persistence",
    version="0.0.4",
    packages=find_packages(),
    install_requires=[
        "injector>=0.19.0",
        "aioredis>=2.0.1",
        "sqlalchemy[mypy]>=1.4.37",
        "aiomysql>=0.1.1",
        "contextvar-request-scope",
        "async_injection_provider",
    ],
)
