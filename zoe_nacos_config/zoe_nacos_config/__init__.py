import asyncio
import dataclasses
import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Tuple, Type, TypeVar, Callable, Coroutine, Optional

import aiohttp
import pydantic
import requests

logger = logging.getLogger("zoe_nacos_config")

T = TypeVar("T", bound=pydantic.BaseModel)

__all__ = ["get_zoe_nacos_config", "NacosConfig", "NacosKey", "listen_nacos_config"]


class NacosSyncRequestor:
    def get(self, url: str, params: Dict[str, Any] = None) -> bytes:
        resp = requests.get(url, params=params, timeout=3)
        return resp.content


class NacosRequestor:
    async def get(self, url: str, params: dict, headers: dict = None) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:
                request_response = await resp.content.read()
                logger.debug(
                    f"NacosRequestor[{id(self)}] "
                    f"Get: url={url}, params={params}, request_response={request_response}"
                )
                return request_response

    async def post(self, url: str, data: dict, headers: dict) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as resp:
                response_content = await resp.content.read()
                logger.debug(
                    f"NacosRequestor [{id(self)}]"
                    f"Post: url={url}, data={data}, headers={headers}, "
                    f"response_content={response_content}"
                )
                return response_content


_WORD_SEPARATOR = "\x02"
_LINE_SEPARATOR = "\x01"


@dataclasses.dataclass(frozen=True)
class NacosConfig:
    address: str
    username: str
    password: str

    long_pulling_timeout_ms: int = 100  # milliseconds


@dataclasses.dataclass
class NacosKey:
    namespace: str
    group: str
    data_id: str

    @classmethod
    def from_listening_config(cls, config: bytes) -> "NacosKey":
        config_str = config.decode("utf-8")
        data_id, group, tenant = config_str.split("%02")
        return cls(tenant, group, data_id)

    def __eq__(self, other):
        return (
            self.namespace == other.namespace
            and self.group == other.group
            and self.data_id == other.data_id
        )

    def __hash__(self):
        return hash((self.namespace, self.group, self.data_id))


@dataclasses.dataclass
class NacosValue:
    key: NacosKey

    current_config: bytes = None
    current_version_md5: str = ""

    def update(self, new_config: bytes):
        self.current_config = new_config
        self.current_version_md5 = hashlib.md5(new_config).hexdigest()

    def as_listening_config(self) -> str:
        return (
            _WORD_SEPARATOR.join(
                [
                    self.key.data_id,
                    self.key.group,
                    self.current_version_md5,
                    self.key.namespace,
                ]
            )
            + _LINE_SEPARATOR
        )

    def as_key(self) -> str:
        return _WORD_SEPARATOR.join(
            [self.key.data_id, self.key.group, self.key.namespace]
        )

    def is_key_equal(self, data_id: str, group: str, namespace: str) -> bool:
        key = self.key
        return (
            key.data_id == data_id and key.group == group and key.namespace == namespace
        )


class NacosConfigManager:
    def __init__(
        self,
        nacos_config: NacosConfig,
        nacos_keys: List[NacosKey],
        requestor: NacosRequestor = NacosRequestor(),
        sync_requestor: NacosSyncRequestor = NacosSyncRequestor(),
    ):
        self.requestor = requestor
        self.sync_requestor = sync_requestor

        self.nacos_config = nacos_config
        self.service_addr = nacos_config.address
        self.username = nacos_config.username
        self.password = nacos_config.password

        self.keys: Dict[NacosKey, NacosValue] = {
            key: NacosValue(key) for key in nacos_keys
        }

        # urls
        self.get_config_url = f"{self.service_addr}/nacos/v1/cs/configs"
        self.listen_config_url = f"{self.service_addr}/nacos/v1/cs/configs/listener"

    def get_config_sync(self, nacos_key: NacosKey) -> bytes:
        params = {
            "dataId": nacos_key.data_id,
            "group": nacos_key.group,
            "tenant": nacos_key.namespace,
        }
        config_bytes = self.sync_requestor.get(self.get_config_url, params)
        return config_bytes

    async def get_config(self, nacos_key: NacosKey) -> bytes:
        params = {
            "dataId": nacos_key.data_id,
            "group": nacos_key.group,
            "tenant": nacos_key.namespace,
        }
        config_bytes = await self.requestor.get(self.get_config_url, params)
        nacos_value = self.keys.get(nacos_key, None)
        if not nacos_value:
            nacos_value = NacosValue(key=nacos_key)
        nacos_value.update(config_bytes)
        return config_bytes

    async def get_config_by_listen(self, nacos_key: NacosKey) -> Optional[bytes]:
        nacos_value = self.keys.get(nacos_key, None)
        if not nacos_value:
            nacos_value = NacosValue(key=nacos_key)

        changed_configs = await self.requestor.post(
            self.listen_config_url,
            data={"Listening-Configs": nacos_value.as_listening_config()},
            headers={"Long-Pulling-Timeout": str(30 * 1000)},  # 30s
        )
        if not changed_configs:
            return
        for changed_config in changed_configs.strip().split(b"%01"):
            updated_nacos_key = NacosKey.from_listening_config(changed_config)
            if not updated_nacos_key:
                return
            return await self.get_config(updated_nacos_key)


def _get_nacos_config_from_env(
    default_nacos_config: dict,
) -> Tuple[NacosConfig, List[NacosKey]]:
    if not default_nacos_config:
        default_nacos_config = {}

    def get_env_or_default(key: str) -> Any:
        return os.environ.get(key, default_nacos_config.get(key))

    nacos_config = NacosConfig(
        address=get_env_or_default("NACOS_ADDRESS"),
        username=get_env_or_default("NACOS_USERNAME"),
        password=get_env_or_default("NACOS_PASSWORD"),
    )

    nacos_key = NacosKey(
        namespace=get_env_or_default("NACOS_NAMESPACE"),
        group=get_env_or_default("NACOS_GROUP"),
        data_id=get_env_or_default("NACOS_DATA_ID"),
    )
    assert (
        nacos_config.address and nacos_key.namespace and nacos_key.group and nacos_key.data_id
    ), "NACOS_* env variables are not set"
    return nacos_config, [nacos_key]


def _packaging_config(config_class: Type[T], dict_config: dict) -> T:
    if not issubclass(config_class, pydantic.BaseModel):
        raise ValueError("[zoe_nacos_config] config_class must be pydantic Model")
    config = config_class.parse_obj(dict_config)
    return config


_update_func: Optional[Callable[[bool], Coroutine]] = None


async def listen_nacos_config(interval_seconds: int = 60, enable_log=True) -> None:
    assert interval_seconds >= 3, "拉取nacos配置请求间隔需大于等于3秒"
    if not _update_func:
        raise RuntimeError("use get_zoe_nacos_config first")
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await _update_func(enable_log)
        except Exception:
            logger.exception("[zoe_nacos_config] get config error")


service_config = None


def get_zoe_nacos_config(
    config_class: Type[T],
    default_nacos_config: dict = None,
) -> T:
    global service_config
    if service_config:
        logger.warning("[zoe_nacos_config] get_zoe_nacos_config 应该只调用一次")
        return service_config

    if not issubclass(config_class, pydantic.BaseModel):
        raise ValueError("[zoe_nacos_config] config_class must be pydantic Model")
    nacos_config, nacos_keys = _get_nacos_config_from_env(default_nacos_config)
    manager = NacosConfigManager(
        nacos_config,
        nacos_keys,
    )
    # asyncio.create_task(manager.start_listen())
    new_config = manager.get_config_sync(nacos_keys[0])
    if not new_config or new_config.startswith(b"config data not exist"):
        print(
            "[zoe_nacos_config] no config found. data_id:{} group:{} namespace:{}".format(
                nacos_keys[0].data_id, nacos_keys[0].group, nacos_keys[0].namespace
            )
        )
        new_config = b"{}"
    try:
        dict_config = json.loads(new_config.decode("utf-8"))
    except Exception as e:
        print(f"[zoe_nacos_config] decode config error: {e}. config: {new_config}")
        exit(-1)
        return

    config_obj = _packaging_config(config_class, dict_config)

    async def listen_remote(enable_log: bool):
        _new_config = await manager.get_config_by_listen(nacos_keys[0])
        if not _new_config:
            logger.debug("[zoe_nacos_config] config not changed")
            return
        _dict_config = json.loads(_new_config.decode("utf-8"))
        _config_obj = _packaging_config(config_class, _dict_config)
        for a in config_class.__annotations__:
            setattr(config_obj, a, getattr(_config_obj, a))
        if enable_log:
            logger.info(f"[zoe_nacos_config] config updated")
            print(f"[zoe_nacos_config] config updated")

    global _update_func
    _update_func = listen_remote

    service_config = config_obj
    return service_config
