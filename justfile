check:
    cd ./dev; nix flake check

fmt:
    cd ./dev; nix fmt ../

develop:
    cd ./dev; nix develop

generate-pre-commit:
    cd ./dev; nix develop .#pre-commit

python-tests:
    poetry run pytest --cov src tests

build-docs:
    nix build .#docs

show-docs:
    nix run .#docs.serve