import "dev/justfile.default"

develop:
    nix develop "{{ justfile_directory() + '#default' }}"

python-tests:
    poetry run pytest --cov src tests

build-docs:
    nix build "{{ justfile_directory() + '#docs' }}"

show-docs:
    nix run "{{ justfile_directory() + '#docs.serve' }}"