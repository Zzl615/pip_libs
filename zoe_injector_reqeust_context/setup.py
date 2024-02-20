from setuptools import find_packages, setup

setup(
    name="zoe_injector_reqeust_context",
    version="0.0.4",
    packages=find_packages(),
    install_requires=[
        "injector>=0.19.0",
        "contextvars",
    ],
)
