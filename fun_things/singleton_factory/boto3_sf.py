from . import SingletonFactory

try:
    import boto3

    _exists = True

except:
    _exists = False


class Boto3SF(SingletonFactory):
    def _instantiate(self):
        if not _exists:
            raise ImportError("You don't have `boto3` installed!")

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
