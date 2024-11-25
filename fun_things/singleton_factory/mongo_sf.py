from . import SingletonFactory
from pymongo import MongoClient


class MongoSF(SingletonFactory[MongoClient]):
    def _instantiate(self):
        mongo = MongoClient(
            *self.args,
            **self.kwargs,
        )

        print("Instantiated MongoDB.", mongo)

        return mongo

    def _destroy(self):
        mongo = self.instance

        mongo.close()

        print("MongoDB destroyed.", mongo)

        return True
