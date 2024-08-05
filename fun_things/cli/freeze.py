import os
import re
from argparse import _SubParsersAction
from configparser import ConfigParser
from typing import List

RX_BITBUCKET = r"^-e git\+https://(.+)@bitbucket\.org\/(.+)\/(.+)\.git@(.+)#egg"
IGNORES = [
    "pkg_resources==0.0.0",
]


def _setup_cfg(args, lines: List[str]):
    if not args.cfg:
        return

    config = ConfigParser(
        allow_no_value=True,
        comment_prefixes=[],
        strict=False,
    )

    config.read(args.cfg_path)

    if not config.has_option("options", "install_requires"):
        return

    text = "\n" + "".join(lines).strip()
    config["options"]["install_requires"] = text

    with open(args.cfg_path, "w") as f:
        config.write(f)

    print(f"Updated `{args.cfg_path}`.")


def _bitbucket(line: str):
    match = re.match(RX_BITBUCKET, line)

    if match == None:
        return None

    access_token = match[1]
    path = match[2]
    name = match[3]
    commit_hash = match[4]

    return (
        f"{name} @ git+https://{access_token}@bitbucket.org/{path}/{name}@{commit_hash}"
    )


def _selector(line: str):
    line = line.strip()

    if line in IGNORES:
        return ""

    bitbucket = _bitbucket(line)

    if bitbucket != None:
        line = bitbucket

    print(line)
    return line + "\r\n"


def _main(args):
    filepath = args.f

    os.system(f"pip freeze > {filepath}")

    with open(filepath, "r") as f:
        lines = f.readlines()
        lines = [*map(_selector, lines)]

    _setup_cfg(args, lines)

    with open(filepath, "w") as f:
        f.writelines(lines)

    print(f"Updated `{filepath}`.")


def freeze(subparsers: _SubParsersAction):
    parser = subparsers.add_parser(
        "freeze",
        help="pip freeze",
    )

    parser.add_argument(
        "-f",
        type=str,
        help="filepath",
        default="requirements.txt",
        required=False,
    )

    parser.add_argument(
        "-cfg",
        type=bool,
        help="If it should write to `setup.cfg`.",
        default=True,
        required=False,
    )
    parser.add_argument(
        "-cfg_path",
        type=str,
        help="Path to `setup.cfg`.",
        default="setup.cfg",
        required=False,
    )

    parser.set_defaults(func=_main)
