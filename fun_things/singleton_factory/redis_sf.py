from . import SingletonFactory

try:
    from redis import Redis

    _exists = True

except:
    _exists = False


class RedisSF(SingletonFactory["Redis"]):
    def _instantiate(self):
        if not _exists:
            raise ImportError("You don't have `redis` installed!")

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
