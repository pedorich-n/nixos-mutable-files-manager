import json
import logging
import os
import shutil
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import PosixPath
from typing import Iterable, List, Optional, Sequence, TypeVar

from expression import Nothing, Option

T = TypeVar("T")

logger = logging.getLogger("manage_files")

logging.basicConfig(
    level=logging.DEBUG,
    format="[{levelname:<5s}] - {message}",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    style="{",
)


@dataclass
class Metadata:
    user: Option[str]
    group: Option[str]
    mode: Option[int]


# region "Helpers"


def try_read_text(path: PosixPath) -> Optional[str]:
    if path.exists():
        return path.read_text()
    else:
        return None


def try_read_lines(path: PosixPath) -> Optional[List[str]]:
    maybe_text = try_read_text(path)
    if maybe_text:
        return maybe_text.splitlines()
    else:
        return None


# endregion


# region "State"
def read_state_or_empty(path: PosixPath) -> List[PosixPath]:
    return [PosixPath(p) for p in (try_read_lines(path) or [])]


def write_state(path: PosixPath, state: Iterable[PosixPath]) -> None:
    with open(path, "w") as file:
        logger.debug(f"Writing state to {str(path)}")
        for line in state:
            file.write(f"{line}\n")


def get_files_to_delete_from_states(old: Iterable[PosixPath], new: Iterable[PosixPath]) -> List[PosixPath]:
    old_set = set(old)
    new_set = set(new)

    result_set = old_set.difference(new_set)

    result = list(result_set)
    result.sort()

    return result


# endregion


# region Files
def get_rel_files_recursively(
    root: PosixPath,
) -> List[PosixPath]:
    files = []
    for dirpath, _, filenames in os.walk(root, followlinks=True):
        for filename in filenames:
            file_path = PosixPath(dirpath).joinpath(filename)
            rel_path = file_path.relative_to(root)
            files.append(rel_path)
    return files


def create_dirs_recursively(
    target_root: PosixPath,
    relative_source_paths: Iterable[PosixPath],
) -> None:
    for relative_source_path in relative_source_paths:
        # Assuming here that all paths are file-paths
        target = target_root.joinpath(relative_source_path.parent)

        logger.debug(f"Creating {target}")
        target.mkdir(exist_ok=True, parents=True, mode=0o777)


def _copy_file(source: PosixPath, destination: PosixPath):
    logger.debug(f"Copying file from {source} to {destination}")
    shutil.copyfile(src=source, dst=destination)


def _chown(path: PosixPath, user: Option[str], group: Option[str]) -> None:
    if user.is_some() or group.is_some():
        logger.debug(f"Setting user:{user}, group:{group} for {path}")
        shutil.chown(path=path, user=user.default_value(None), group=group.default_value(None))  # type: ignore


def _chmod(path: PosixPath, maybe_mode: Option[int]) -> None:
    def inner(mode: int):
        logger.debug(f"Setting mode: {mode} for {path}")
        os.chmod(path, mode)

    maybe_mode.map(inner)


def copy_files_and_set_permissions_from_rel(
    source_root: PosixPath,
    destination_root: PosixPath,
    metadata_root: PosixPath,
    rel_paths: Iterable[PosixPath],
) -> None:
    for path in rel_paths:
        source_abs_path = source_root.joinpath(path)
        destination_abs_path = destination_root.joinpath(path)
        metadata_abs_path = metadata_root.joinpath(f"{path}.meta")  # TODO: get rid of .meta?

        metadata = _try_get_metadata(metadata_abs_path)

        _copy_file(source=source_abs_path, destination=destination_abs_path)
        _chmod(path=destination_abs_path, maybe_mode=metadata.mode)
        _chown(path=destination_abs_path, user=metadata.user, group=metadata.group)


def remove_files(paths: Iterable[PosixPath]):
    for path in paths:
        if path.exists():
            logger.debug(f"Removing file {str(path)}")
            path.unlink()


def _try_get_metadata(path: PosixPath) -> Metadata:
    def non_empty(value: str) -> bool:
        return value.strip() != ""

    def build_metadata(value: str) -> Metadata:
        parsed = json.loads(value)

        metadata = Metadata(
            user=Option.of_optional(parsed.get("user")).filter(non_empty),
            group=Option.of_optional(parsed.get("group")).filter(non_empty),
            mode=Option.of_optional(parsed.get("mode")).filter(non_empty).map(lambda value: int(value, 8)),
        )
        return metadata

    maybe_text = Option.of_optional(try_read_text(path)).filter(non_empty)
    metadata = maybe_text.map(build_metadata).default_value(Metadata(Nothing, Nothing, Nothing))
    logger.debug(f"Metadata for {path} is {metadata}")
    return metadata


# endregion


def main(argv: Optional[Sequence[str]] = None):
    parser = ArgumentParser("Manage mutable files with NixOS module")
    parser.add_argument("--source", type=PosixPath, required=True)
    parser.add_argument("--destination", type=PosixPath, required=True)
    parser.add_argument("--metadata", type=PosixPath, required=True)
    parser.add_argument("--state", type=PosixPath, required=True)

    args = parser.parse_args(args=argv)

    source: PosixPath = args.source
    destination: PosixPath = args.destination
    metadata: PosixPath = args.metadata
    state_path: PosixPath = args.state

    source_files = get_rel_files_recursively(source)
    logger.debug(f"Source files: {source_files}")

    create_dirs_recursively(destination, source_files)

    old_state = read_state_or_empty(state_path)
    logger.debug(f"Old state is {old_state}")

    copy_files_and_set_permissions_from_rel(
        source_root=source, destination_root=destination, metadata_root=metadata, rel_paths=source_files
    )

    new_state = [destination.joinpath(p) for p in source_files]
    logger.debug(f"New state is {[str(path) for path in new_state]}")

    files_to_delete = get_files_to_delete_from_states(old_state, new_state)
    logger.debug(f"Files to delete {files_to_delete}")

    remove_files(files_to_delete)

    write_state(state_path, new_state)

