from argparse import ArgumentParser
import logging
import os
import shutil
from pathlib import PosixPath
from typing import Iterable, List, Optional, TypeVar, Sequence

T = TypeVar("T")

logger = logging.getLogger("manage_files")

logging.basicConfig(
    level=logging.DEBUG,
    format="[{levelname:<5s}] - {message}",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    style="{",
)


# region "State"
def read_state_or_empty(path: PosixPath) -> List[PosixPath]:
    if path.exists():
        with open(path, "r") as file:
            return [PosixPath(path) for path in file.read().splitlines()]
    else:
        return []


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


def copy_files_from_rel(
    source_root: PosixPath,
    destination_root: PosixPath,
    rel_paths: Iterable[PosixPath],
) -> None:
    for path in rel_paths:
        source_abs_path = source_root.joinpath(path)
        destination_abs_path = destination_root.joinpath(path)
        _copy_file(
            source=source_abs_path,
            destination=destination_abs_path,
        )


def remove_files(paths: Iterable[PosixPath]):
    for path in paths:
        logger.debug(f"Removing file {str(path)}")
        path.unlink()


# endregion


def main(argv: Optional[Sequence[str]] = None):
    parser = ArgumentParser("Manage mutable files with NixOS module")
    parser.add_argument("--source", type=PosixPath, required=True)
    parser.add_argument("--destination", type=PosixPath, required=True)
    parser.add_argument("--state", type=PosixPath, required=True)

    args = parser.parse_args(args=argv)

    source: PosixPath = args.source
    destination: PosixPath = args.destination
    state_path: PosixPath = args.state

    source_files = get_rel_files_recursively(source)
    logger.debug(f"Source files: {source_files}")

    create_dirs_recursively(destination, source_files)

    old_state = read_state_or_empty(state_path)
    logger.debug(f"Old state is {old_state}")

    copy_files_from_rel(source_root=source, destination_root=destination, rel_paths=source_files)

    # TODO: generate new state from copy_files_from_rel response, once it handles errors
    new_state = [destination.joinpath(p) for p in source_files]
    logger.debug(f"New state is {new_state}")

    files_to_delete = get_files_to_delete_from_states(old_state, new_state)
    logger.debug(f"Files to delete {files_to_delete}")

    remove_files(files_to_delete)

    write_state(state_path, new_state)


# if __name__ == "__main__":
#     main()
