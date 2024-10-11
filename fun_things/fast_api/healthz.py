from enum import Enum
from typing import List, Optional

try:
    from fastapi_healthz import (
        HealthCheckAbstract,
    )
    from fastapi_healthz.models import HealthCheckStatusEnum
    from redis import Redis
    from redis.retry import Retry
    from redis.exceptions import TimeoutError, ConnectionError
    from redis.backoff import ExponentialBackoff

    _ok = True
except:

    class HealthCheckAbstract:
        pass

    class HealthCheckStatusEnum(Enum):
        pass

    _ok = False


class HealthCheckRedis2(HealthCheckAbstract):
    def __init__(
        self,
        host: str,
        port: int,
        password: Optional[str] = None,
        service: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ):
        if not _ok:
            raise ImportError("`fastapi-healthz` and `redis` is required!")

        super().__init__(service, tags)

        self.__host = host
        self.__port = port
        self.__password = password

    @property
    def service(self) -> str:
        return self._service if self._service is not None else "redis"

    @property
    def connection_uri(self) -> Optional[str]:
        return f"redis://{self.__password + '@' if self.__password else ''}{self.__host}:{self.__port}"

    def check_health(self) -> HealthCheckStatusEnum:
        try:
            redis = Redis(
                host=self.__host,
                port=self.__port,
                password=self.__password,
                retry=Retry(ExponentialBackoff(cap=60, base=1), 25),
                retry_on_error=[
                    ConnectionError,
                    TimeoutError,
                    ConnectionResetError,
                ],
                health_check_interval=60,
            )

            ok = redis.ping()

            return (
                HealthCheckStatusEnum.HEALTHY if ok else HealthCheckStatusEnum.UNHEALTHY
            )

        except:
            return HealthCheckStatusEnum.UNHEALTHY
