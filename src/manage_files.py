from argparse import ArgumentParser
import logging
import os
import shutil
from pathlib import PosixPath
from typing import Callable, Iterable, List, Optional, TypeVar, Sequence

T = TypeVar("T")

logger = logging.getLogger("manage_files")

logging.basicConfig(
    level=logging.DEBUG,
    format="[{asctime}] [{levelname:<5s}] [{name}:{lineno:03}] - {message}",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    style="{",
)


def _dry_run_wrap(callable: Callable[[], T], dry_run: bool) -> Optional[T]:
    if dry_run:
        return None
    else:
        return callable()


# region "State"
def read_state_or_empty(path: PosixPath) -> List[PosixPath]:
    if path.exists():
        with open(path, "r") as file:
            return [PosixPath(path) for path in file.read().splitlines()]
    else:
        return []


def write_state(path: PosixPath, state: Iterable[PosixPath], dry_run: bool) -> None:
    def inner():
        with open(path, "w") as file:
            for line in state:
                file.write(f"{line}\n")

    return _dry_run_wrap(inner, dry_run)


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
    dry_run: bool,
) -> None:
    for relative_source_path in relative_source_paths:
        # Assuming here that all paths are file-paths
        target = target_root.joinpath(relative_source_path.parent)

        logger.info(f"Creating {target}")
        _dry_run_wrap(
            lambda: target.mkdir(exist_ok=True, parents=True, mode=0o777),
            dry_run,
        )


def _copy_file(source: PosixPath, destination: PosixPath, dry_run: bool):
    prefix = "[DRY_RUN] " if dry_run else ""
    logger.debug(f"{prefix}Copying file from {source} to {destination}")
    _dry_run_wrap(
        lambda: shutil.copyfile(src=source, dst=destination),
        dry_run,
    )


def copy_files_from_rel(
    source_root: PosixPath,
    destination_root: PosixPath,
    rel_paths: Iterable[PosixPath],
    dry_run: bool,
) -> None:
    for path in rel_paths:
        source_abs_path = source_root.joinpath(path)
        destination_abs_path = destination_root.joinpath(path)
        _copy_file(
            source=source_abs_path,
            destination=destination_abs_path,
            dry_run=dry_run,
        )


def remove_files(paths: Iterable[PosixPath], dry_run: bool):
    def inner():
        for path in paths:
            path.unlink()

    _dry_run_wrap(lambda: inner(), dry_run)


# endregion


def main(argv: Optional[Sequence[str]] = None):
    parser = ArgumentParser("")
    parser.add_argument("--source", type=PosixPath, required=True)
    parser.add_argument("--destination", type=PosixPath, required=True)
    # TODO: fix state path
    parser.add_argument("--state", type=PosixPath, default=PosixPath("/var/lib/test/state"), required=False)
    parser.add_argument("--dry-run", action="store_true", default=False, required=False)
    args = parser.parse_args(args=argv)

    source: PosixPath = args.source
    destination: PosixPath = args.destination
    state_path: PosixPath = args.state
    dry_run: bool = args.dry_run

    source_files = get_rel_files_recursively(source)
    logger.debug(f"Source files: {source_files}")

    create_dirs_recursively(destination, source_files, dry_run)

    old_state = read_state_or_empty(state_path)
    logger.debug(f"Old state is {old_state}")

    copy_files_from_rel(source_root=source, destination_root=destination, rel_paths=source_files, dry_run=dry_run)

    # TODO: generate new state from copy_files_from_rel response, once it handles errors
    new_state = [destination.joinpath(p) for p in source_files]
    logger.debug(f"New state is {new_state}")

    files_to_delete = get_files_to_delete_from_states(old_state, new_state)
    logger.debug(f"Files to delete {files_to_delete}")

    remove_files(files_to_delete, dry_run)

    write_state(state_path, new_state, dry_run)


# if __name__ == "__main__":
#     main()
