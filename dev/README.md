# Development environment

Dev environment is provided as a separate `flake.nix` file to reduce the number of inputs propagated to the upstream users.
This approach is inspired by https://github.com/nix-community/ethereum.nix/issues/258

Both benefit and the downside is that there are two separate lock files now. So it's now possible to have a discrepancy between the development and release environments.
