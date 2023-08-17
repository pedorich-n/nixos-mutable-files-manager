{
  description = "Application packaged using poetry2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    systems.url = "github:nix-systems/default";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };

    pre-commit-hooks = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
    };

    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
    };
  };

  outputs = inputs@{ flake-parts, systems, ... }: flake-parts.lib.mkFlake { inherit inputs; } {
    systems = import systems;
    imports = [
      inputs.pre-commit-hooks.flakeModule
    ];

    perSystem = { config, inputs', pkgs, system, ... }: {
      _module.args.pkgs = import inputs.nixpkgs {
        inherit system;
        overlays = [ inputs.poetry2nix.overlay ];
      };

      packages = {
        default = pkgs.callPackage ./nix/package.nix { };
        docs = pkgs.callPackage ./nix/docs.nix { };
      };

      devShells = {
        default = pkgs.mkShell {
          name = "nixos-mutable-files-manager";
          buildInputs = [ pkgs.bashInteractive ];
          packages = [
            inputs'.poetry2nix.packages.poetry
            pkgs.just
          ];
        };

        pre-commit = config.pre-commit.devShell;
      };


      pre-commit.settings.hooks = {
        # Nix
        deadnix.enable = true;
        nixpkgs-fmt.enable = true;
        statix.enable = true;

        # Python
        black = {
          enable = true;
          entry = with pkgs; lib.mkForce "${lib.getExe black} --line-length=120";
        };
        isort.enable = true;

        # Other
        prettier = {
          enable = true;
          files = ".+\.md";
        };
      };
    };
    flake = {
      nixosModules.default = import ./nix/nixos-module.nix;
    };
  };
}
