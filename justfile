check:
    nix flake check

fmt: 
    nix fmt

python-tests:
    poetry run pytest --cov src tests

build-docs:
    nix build .#docs

show-docs:
    nix run .#docs.serve

# run *ARGS='':
#     poetry  run -- {{ARGS}}