{
  description = "Application packaged using poetry2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";


    # Dev tools
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs@{ flake-parts, systems, ... }: flake-parts.lib.mkFlake { inherit inputs; } {
    systems = import systems;
    imports = [
      inputs.treefmt-nix.flakeModule
    ];

    perSystem = { config, self', inputs', pkgs, system, ... }: {
      _module.args.pkgs = import inputs.nixpkgs {
        inherit system;
        overlays = [ inputs.poetry2nix.overlay ];
      };

      packages = {
        default = pkgs.callPackage ./nix/package.nix { };
      };

      devShells.default = pkgs.mkShell {
        name = "nixos-mutable-files-manager";
        buildInputs = [ pkgs.bashInteractive ];
        packages = [
          inputs'.poetry2nix.packages.poetry
          pkgs.just
        ];
      };

      # https://numtide.github.io/treefmt/
      treefmt.config = {
        projectRootFile = "flake.nix";
        programs = {
          nixpkgs-fmt.enable = true;
          black.enable = true;
        };
        settings.formatter = {
          black.options = [ "--line-length=120" ];
        };
      };
    };
    flake = {
      nixosModules.default = import ./nix/nixos-module.nix;
    };
  };
}
