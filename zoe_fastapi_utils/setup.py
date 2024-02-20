from setuptools import find_packages, setup

setup(
    name="zoe_fastapi_utils",
    version="0.0.8.dev3",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.78.0",
    ],
)
