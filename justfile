fmt: 
    nix fmt

python-tests:
    poetry run pytest --cov src tests

# run *ARGS='':
#     poetry  run -- {{ARGS}}