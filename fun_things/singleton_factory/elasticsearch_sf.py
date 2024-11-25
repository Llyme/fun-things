from . import SingletonFactory
from elasticsearch import Elasticsearch


class ElasticsearchSF(SingletonFactory[Elasticsearch]):
    def _instantiate(self):
        es = Elasticsearch(
            *self.args,
            **self.kwargs,
        )

        print("Instantiated Elasticsearch.", es)

        return es

    def _destroy(self):
        es = self.instance

        es.close()

        print("Elasticsearch destroyed.", es)

        return True
