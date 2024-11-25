from . import SingletonFactory
from redis import Redis


class RedisSF(SingletonFactory[Redis]):
    def _instantiate(self):
        redis = Redis(
            *self.args,
            **self.kwargs,
        )

        print("Instantiated Redis.", redis)

        return redis

    def _destroy(self):
        redis = self.instance

        redis.close()

        print("Redis destroyed.", redis)

        return True
