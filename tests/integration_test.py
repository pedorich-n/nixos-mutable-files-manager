from pathlib import PosixPath
import src.manage_files as manage_files
from tests.helpers import assert_file_content


def test_program_add_files(tmp_path):
    tmp_source = tmp_path / "source"
    tmp_source.mkdir()

    tmp_destination = tmp_path / "destination"
    tmp_destination.mkdir()

    tmp_state = tmp_path / "state.txt"
    tmp_state.write_text("")

    (tmp_source / "1.txt").write_text("test1")
    (tmp_source / "2" / "3").mkdir(parents=True)
    (tmp_source / "2" / "4.txt").write_text("test2")
    (tmp_source / "2" / "3" / "5.txt").write_text("test3")
    (tmp_source / "6").mkdir()
    (tmp_source / "6" / "7.txt").write_text("test4")

    args = ["--source", str(tmp_source), "--destination", str(tmp_destination), "--state", str(tmp_state)]
    manage_files.main(args)

    assert_file_content((tmp_destination / "1.txt"), ["test1"])
    assert_file_content((tmp_destination / "2" / "4.txt"), ["test2"])
    assert_file_content((tmp_destination / "2" / "3" / "5.txt"), ["test3"])
    assert_file_content((tmp_destination / "6" / "7.txt"), ["test4"])

    expected_state = [str(tmp_destination.joinpath(PosixPath(p))) for p in ["1.txt", "2/4.txt", "2/3/5.txt", "6/7.txt"]]

    assert_file_content(tmp_state, expected_state, sort=True)


def test_program_add_update_delete_files(tmp_path):
    tmp_source = tmp_path / "source"
    tmp_source.mkdir()

    tmp_destination = tmp_path / "destination"
    tmp_destination.mkdir()

    (tmp_source / "1.txt").write_text("test1")
    (tmp_source / "2" / "3").mkdir(parents=True)
    (tmp_source / "2" / "4.txt").write_text("test2")
    (tmp_source / "2" / "3" / "5.txt").write_text("test3")
    (tmp_source / "6").mkdir()
    (tmp_source / "6" / "7.txt").write_text("test4")

    (tmp_destination / "1.txt").write_text("test11")
    (tmp_destination / "6").mkdir()
    (tmp_destination / "6" / "8.txt").write_text("test5")
    old_state = "\n".join([str(tmp_destination.joinpath(PosixPath(p))) for p in ["1.txt", "6/8.txt"]])

    tmp_state = tmp_path / "state.txt"
    tmp_state.write_text(old_state)

    args = ["--source", str(tmp_source), "--destination", str(tmp_destination), "--state", str(tmp_state)]
    manage_files.main(args)

    assert_file_content((tmp_destination / "1.txt"), ["test1"])
    assert_file_content((tmp_destination / "2" / "4.txt"), ["test2"])
    assert_file_content((tmp_destination / "2" / "3" / "5.txt"), ["test3"])
    assert_file_content((tmp_destination / "6" / "7.txt"), ["test4"])
    assert (tmp_destination / "6" / "8.txt").exists() == False

    expected_state = [str(tmp_destination.joinpath(PosixPath(p))) for p in ["1.txt", "2/4.txt", "2/3/5.txt", "6/7.txt"]]

    assert_file_content(tmp_state, expected_state, sort=True)
