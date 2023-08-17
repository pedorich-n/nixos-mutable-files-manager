# NixOS Mutable Files Manager

## Problem

When you manage files with Nix, they are stored in the immutable storage at `/nix/store/`. And there's no way to change the file other than switch the configuration.
While this solution allows better control over files and reproducibility, sometimes it causes inconvenience. For example when files aren't "stable" yet and require changes, or they might get edited by an external process.
There's no straightforward built-in solution to this problem.

## Solution

This module provides a way to manage mutable files anywhere on the File System with Nix. It is done by copying files directly to the destination instead of symlinking from `/nix/store/`.

The algorithm for the program is pretty simple:

- link all files from `environment.mutable-files` into a single Nix derivation
- get tree structure for these files
- create all the necessary folders on File System
- read previous state (list of files), if available from `/var/lib/mutable-files/state.txt`
- copy all files to File System
- apply owner & permissions changes if needed
- diff old state and new state
- remove any files not present in the new state
- write new state to `/var/lib/mutable-files/state.txt`

While mutable files go against the Nix philosophy, this module provides a compromise that avoids the need to switch your entire NixOS configuration just for temporary changes.

The module was heavily inspired by [environment.etc](https://search.nixos.org/options?channel=unstable&show=environment.etc&query=environment.etc).

## Warning

When using this module:

- Exercise caution when modifying files.
- There is no backup mechanism for files.
- The module overwrites files on the file system without confirmation.
- As it runs with `root` privileges, it can potentially overwrite any file.

## Getting Started

To include this module in your NixOS configuration, add the following to your `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixos-mutable-files-manager.url = "github:pedorich-n/nixos-mutable-files-manager";
  };

  outputs = { self, nixpkgs, nixos-mutable-files-manager }: {
    nixosConfigurations.example = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        nixos-mutable-files-manager.nixosModules.default
        ./configuration.nix
      ];
    };
  };
}
```

`configuration.nix`:

```nix
{pkgs, ...}: {
  ...
  environment.mutable-files = {
    "/opt/example/config.yml" = {
      source = ./config.yml;
      user = "nobody";
      group = "users";
      mode = "664";
    };
  };
}
```

## Documentation

Full documentation is at [docs/module.md](docs/module.md)
