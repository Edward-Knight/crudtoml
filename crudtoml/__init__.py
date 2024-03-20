"""Perform CRUD operations on TOML files.

A command-line interface for reading and editing TOML documents
in a style-preserving way.
"""
import argparse
import copy
import functools
import logging
import logging.config
import os
import pathlib
import shlex
import sys
import typing
from typing import NoReturn

import tomlkit
import tomlkit.exceptions
from tomlkit.items import Item


__version__ = "0.1.1"


class ColorfulFormatter(logging.Formatter):
    """Formatter that adds ANSI color escape codes based off of logging level.

    Also lowercases the LogRecord "levelname".
    """

    COLOR_END = "\033[0m"
    COLORS = {
        logging.DEBUG: "\033[35m",  # purple
        logging.INFO: "\033[92m",  # green
        logging.WARNING: "\033[33m",  # yellow
        logging.ERROR: "\033[31;1m",  # red and bold
        logging.CRITICAL: "\033[31;1m",  # red and bold
    }

    def format(self, record: logging.LogRecord) -> str:
        # lowercase the level name
        record = copy.copy(record)
        record.levelname = record.levelname.lower()
        # perform usual formatting
        result = super().format(record)
        # wrap formatted message with ANSI color escapes
        color = None if "NO_COLOR" in os.environ else self.COLORS.get(record.levelno)
        if color is None:
            return result
        else:
            return color + result + self.COLOR_END


class CrudtomlError(Exception):
    """Base exception for this class.

    Provides a user-friendly error message.
    """


TOMLType = dict[str | int, "TOMLType"] | list["TOMLType"] | Item
TOMLContainer = dict[str | int, TOMLType] | list[TOMLType]


@functools.lru_cache(1)
def get_logger() -> logging.Logger:
    return logging.getLogger("crudtoml")


def configure_logging(debug: bool) -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "colorful": {
                    "()": ColorfulFormatter,
                    "fmt": "crudtoml: %(levelname)s: %(message)s",
                },
            },
            "handlers": {
                "stderr": {
                    "class": "logging.StreamHandler",
                    "formatter": "colorful",
                    "level": "DEBUG" if debug else "INFO",
                },
            },
            "loggers": {
                "crudtoml": {
                    "handlers": ["stderr"],
                    "level": "DEBUG",
                },
            },
        }
    )


def resolve_path(doc: TOMLContainer, path: list[str], create: bool = False) -> TOMLType:
    logger = get_logger()
    last_path = "the document root"
    subdoc: TOMLType = doc
    for pathlet in path:
        logger.debug(f"resolving '{pathlet}'")
        if isinstance(subdoc, list):
            logger.debug(f"resolving '{pathlet}' as an index")
            try:
                subdoc = subdoc[int(pathlet)]
            except ValueError:
                raise CrudtomlError(
                    f"cannot interpret '{pathlet}' as an integer index into {last_path}"
                )
            except IndexError:
                # mypy forgets that subdoc is a list here
                subdoc = typing.cast(list[TOMLType], subdoc)
                if create:
                    subdoc.append({})
                    subdoc = subdoc[-1]
                else:
                    raise CrudtomlError(
                        f"'{pathlet}' is not a valid index into {last_path} "
                        f"(length {len(subdoc)})"
                    )
        elif isinstance(subdoc, dict):
            try:
                subdoc = subdoc[pathlet]
            except KeyError:
                # mypy forgets that subdoc is a dict here
                subdoc = typing.cast(dict[str | int, TOMLType], subdoc)
                if create:
                    logger.debug(f"creating table for '{pathlet}'")
                    subdoc[pathlet] = {}
                    subdoc = subdoc[pathlet]
                else:
                    raise CrudtomlError(f"cannot find '{pathlet}' in {last_path}")
        else:
            raise CrudtomlError(
                f"cannot find '{pathlet}' in {last_path} as it is not a collection"
            )
        last_path = f"'{pathlet}'"
    return subdoc


def format_raw(doc: TOMLType | str | int) -> str:
    if isinstance(doc, dict):
        return "\n".join(f"{format_raw(k)}={format_raw(v)}" for k, v in doc.items())
    if isinstance(doc, list):
        return "\n".join(format_raw(v) for v in doc)
    return shlex.quote(str(doc))


def main(argv: list[str] | None = None) -> NoReturn:
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--in-place", action="store_true")
    parser.add_argument(
        "-r",
        "--raw",
        action="store_true",
        help="instead of outputting TOML, output raw values",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("toml_file")

    op_subparsers = parser.add_subparsers(title="operation", dest="op", required=True)

    def add_path(p: argparse.ArgumentParser) -> None:
        p.add_argument("path", nargs="*")

    def add_key(p: argparse.ArgumentParser) -> None:
        p.add_argument("key")

    def add_value(p: argparse.ArgumentParser) -> None:
        p.add_argument("value", type=tomlkit.value)

    create_parser = op_subparsers.add_parser("create")
    add_path(create_parser)
    add_key(create_parser)
    add_value(create_parser)

    read_parser = op_subparsers.add_parser("read")
    add_path(read_parser)

    update_parser = op_subparsers.add_parser("update")
    add_path(update_parser)
    add_key(update_parser)
    add_value(update_parser)

    delete_parser = op_subparsers.add_parser("delete")
    add_path(delete_parser)
    add_key(delete_parser)

    args = parser.parse_args(argv)
    if args.in_place and args.toml_file == "-":
        parser.error("argument -i/--in-place is invalid when input file is '-' (stdin)")
    configure_logging(args.verbose)
    logger = get_logger()
    logger.debug(f"crudtoml called with arguments: {args.__dict__}")

    # read TOML file as doc
    try:
        if args.toml_file == "-":
            doc = tomlkit.load(sys.stdin)
        else:
            doc = tomlkit.parse(pathlib.Path(args.toml_file).read_text())
    except tomlkit.exceptions.ParseError as e:
        err_msg = str(e)
        err_msg = err_msg[0].lower() + err_msg[1:]
        logger.error(f"TOML file invalid: {err_msg}")
        sys.exit(1)
    except OSError as e:
        err_msg = e.strerror[0].lower() + e.strerror[1:]
        logger.error(f"error reading TOML file: {err_msg}")
        sys.exit(1)

    # resolve the specified path by recursing through doc
    try:
        subdoc = resolve_path(doc, args.path, create=args.op == "create")
    except CrudtomlError as e:
        logger.error(e)
        sys.exit(1)

    # last_path is used for nice error messages
    last_path = "the document root"
    if len(args.path) > 0:
        last_path = f"'{args.path[-1]}'"

    if args.op == "read":
        # work already done by resolve_path
        result = subdoc
    else:
        result = doc
        if isinstance(subdoc, dict):
            try:
                if args.op == "create":
                    if args.key in subdoc:
                        logger.error(f"key '{args.key}' already exists in {last_path}")
                        sys.exit(1)
                    subdoc[args.key] = args.value
                elif args.op == "update":
                    subdoc[args.key] = args.value
                elif args.op == "delete":
                    del subdoc[args.key]
            except KeyError:
                logger.error(f"key '{args.key}' does not exist in {last_path}")
                sys.exit(1)
        elif isinstance(subdoc, list):
            logger.debug(f"resolving '{args.key}' as an index")
            try:
                index = int(args.key)
            except ValueError:
                logger.error(
                    f"cannot interpret key '{args.key}' as an integer index "
                    f"into {last_path}"
                )
                sys.exit(1)
            try:
                if args.op == "create":
                    try:
                        subdoc[index] = args.value
                    except IndexError:
                        subdoc.append(args.value)
                elif args.op == "update":
                    subdoc[index] = args.value
                elif args.op == "delete":
                    del subdoc[index]
            except IndexError:
                logger.error(
                    f"key '{args.key}' is not a valid index "
                    f"into {last_path} (length {len(subdoc)})"
                )
                sys.exit(1)
        else:
            logger.error(
                f"cannot access key {args.key} on {last_path} as it is not a collection"
            )
            sys.exit(1)

    # format modified TOML for output
    if args.raw:
        output = format_raw(result) + "\n"
    else:
        # tomlkit.dump has incorrect type hint
        output = tomlkit.dumps(result)  # type: ignore[arg-type]

    # write output
    try:
        if args.in_place:
            pathlib.Path(args.toml_file).write_text(output)
        else:
            sys.stdout.write(output)
    except OSError as e:
        err_msg = e.strerror[0].lower() + e.strerror[1:]
        logger.error(f"error writing TOML file: {err_msg}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
