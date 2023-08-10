from pathlib import PosixPath
from typing import List

import src.manage_files as manage_files
from tests.helpers import assert_file_content


# region State
def test_read_state_or_empty_exists(tmp_path):
    state = "1.txt\n2.txt\n3.txt\n"

    state_path = tmp_path / "state"
    state_path.write_text(state)

    result = manage_files.read_state_or_empty(state_path)

    expected = [PosixPath(p) for p in ["1.txt", "2.txt", "3.txt"]]
    assert result == expected


def test_read_state_or_empty_not_exists(tmp_path):
    state_path = tmp_path / "state"

    result = manage_files.read_state_or_empty(state_path)

    expected = []
    assert result == expected


def test_write_state(tmp_path):
    state = [PosixPath(p) for p in ["1.txt", "2.txt", "3.txt"]]

    state_path = tmp_path / "state"

    manage_files.write_state(state_path, state, False)

    assert state_path.exists() == True
    assert_file_content(state_path, ["1.txt", "2.txt", "3.txt"])


def test_get_files_to_delete_from_states():
    old_state = [PosixPath(p) for p in ["1.txt", "2.txt", "3.txt", "4.txt"]]
    new_state = [PosixPath(p) for p in ["1.txt", "2.txt", "5.txt"]]

    result = manage_files.get_files_to_delete_from_states(old_state, new_state)
    expected = [PosixPath(p) for p in ["3.txt", "4.txt"]]

    assert result == expected


# endregion


# region Files
def test_get_rel_files_recursively(tmp_path):
    (tmp_path / "1").mkdir()
    (tmp_path / "1" / "2.txt").write_text("")
    (tmp_path / "1" / "3").mkdir()
    (tmp_path / "1" / "3" / "4.txt").write_text("")

    result = manage_files.get_rel_files_recursively(tmp_path)

    expected = [
        PosixPath("1/2.txt"),
        PosixPath("1/3/4.txt"),
    ]

    assert result == expected


def test_create_dirs_recursively(tmp_path):
    relative_paths = [PosixPath(p) for p in ["1/2.txt", "1/3/4.txt", "5/6/7.txt"]]

    manage_files.create_dirs_recursively(tmp_path, relative_paths, False)

    assert (tmp_path / "1").exists() == True
    assert (tmp_path / "1" / "3").exists() == True
    assert (tmp_path / "5" / "6").exists() == True


def test__copy_file(tmp_path):
    (tmp_path / "source").mkdir()
    source = tmp_path / "source" / "file.txt"
    source.write_text("test")

    (tmp_path / "destination").mkdir()
    destination = tmp_path / "destination" / "file.txt"

    assert destination.exists() == False

    manage_files._copy_file(source, destination, False)

    assert destination.exists() == True
    assert_file_content(destination, ["test"])


def test_copy_files_from_rel(tmp_path):
    source_folder = tmp_path / "source"
    source_folder.mkdir(parents=True)

    (source_folder / "1.txt").write_text("one")
    (source_folder / "2.txt").write_text("two")
    (source_folder / "3").mkdir()
    (source_folder / "3" / "4.txt").write_text("four")

    destination_folder = tmp_path / "destination"
    (destination_folder / "3").mkdir(parents=True)

    relative_paths = [PosixPath(path) for path in ["1.txt", "2.txt", "3/4.txt"]]

    manage_files.copy_files_from_rel(
        source_root=source_folder,
        destination_root=destination_folder,
        rel_paths=relative_paths,
        dry_run=False,
    )

    assert_file_content((destination_folder / "1.txt"), ["one"])
    assert_file_content((destination_folder / "2.txt"), ["two"])
    assert_file_content((destination_folder / "3" / "4.txt"), ["four"])


def test_remove_files(tmp_path):
    (tmp_path / "1").mkdir()
    (tmp_path / "1" / "2.txt").write_text("")
    (tmp_path / "1" / "3").mkdir()
    (tmp_path / "1" / "3" / "4.txt").write_text("")

    paths = [tmp_path.joinpath(PosixPath(p)) for p in ["1/2.txt", "1/3/4.txt"]]

    assert (tmp_path / "1" / "2.txt").exists() == True
    assert (tmp_path / "1" / "3" / "4.txt").exists() == True

    manage_files.remove_files(paths, False)

    assert (tmp_path / "1" / "2.txt").exists() == False
    assert (tmp_path / "1" / "3" / "4.txt").exists() == False


# endregion
