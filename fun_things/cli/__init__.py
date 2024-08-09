import argparse
from .freeze import Freeze


def cli():
    parser = argparse.ArgumentParser(
        description="Pub/Sub consumer common.",
    )

    Freeze().run(
        parser.add_subparsers(
            dest="command",
        )
    )

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
        return

    parser.print_help()
