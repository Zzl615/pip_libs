from setuptools import find_packages, setup

setup(
    name="zoe_injector_event_bus",
    version="0.0.3",
    packages=find_packages(),
    install_requires=[
        "eventware==0.0.5.1",
        "aio_pika",
        "async_injection_provider",
    ],
)
