{
  description = "Application packaged using poetry2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    systems.url = "github:nix-systems/default";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };

    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs = {
        systems.follows = "systems";
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
        nix-github-actions.follows = "";
        treefmt-nix.follows = "";
      };
    };
  };

  outputs = inputs@{ flake-parts, ... }: flake-parts.lib.mkFlake { inherit inputs; } ({ moduleWithSystem, ... }: {
    systems = import inputs.systems;

    perSystem = { pkgs, system, ... }: {
      _module.args.pkgs = import inputs.nixpkgs {
        inherit system;
        overlays = [ inputs.poetry2nix.overlays.default ];
      };

      packages = {
        default = pkgs.callPackage ./nix/package.nix { };
        docs = pkgs.callPackage ./nix/docs.nix { };
      };

      devShells = {
        default = pkgs.mkShell {
          name = "nixos-mutable-files-manager";
          buildInputs = [ pkgs.bashInteractive ];
          packages = with pkgs; [
            poetry
            just
          ];
        };
      };
    };

    flake = {
      nixosModules.default = moduleWithSystem (perSystem@{ config }: { ... }: {
        imports = [ (import ./nix/nixos-module.nix { package = perSystem.config.packages.default; }) ];
      });
    };
  });
}
