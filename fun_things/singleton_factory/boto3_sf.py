from . import SingletonFactory
import boto3


class Boto3SF(SingletonFactory):
    def _instantiate(self):
        b3 = boto3.client(
            *self.args,
            **self.kwargs,
        )

        print("Instantiated Boto3.", b3)

        return b3

    def _destroy(self):
        b3 = self.instance

        b3.close()

        print("Boto3 destroyed.", b3)

        return True
