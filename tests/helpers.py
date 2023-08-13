from pathlib import PosixPath
from typing import List


def assert_file_content(path: PosixPath, content: List[str], sort: bool = False):
    assert path.exists() == True
    with open(path, "r") as file:
        lines = file.read().splitlines()
        if sort:
            lines.sort()
            content.sort()
        assert lines == content
