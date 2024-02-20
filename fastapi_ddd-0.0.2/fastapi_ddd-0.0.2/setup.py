from setuptools import find_packages, setup

setup(
    name="fastapi_ddd",
    version="0.0.2",
    packages=find_packages(),
    install_requires=[
        # "loguru",
        "SQLAlchemy>=1.4.32",
        "injector>=0.19.0",
        "fastapi>=0.75.0",
        # "aiomysql",
        # "aiohttp",
        # "fastapi",
        # "uvicorn",
        # "fastapi-utils",
        # "pydantic",
        # "openpyxl",
        # "python-multipart",
        # "arrow",
    ],
)
