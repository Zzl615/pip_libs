from setuptools import find_packages, setup

setup(
    name="zoe_nacos_config",
    version="0.2.4",
    packages=find_packages(),
    install_requires=["aiohttp~=3.8.1", "requests", "pydantic>=1.9.0"],
)
