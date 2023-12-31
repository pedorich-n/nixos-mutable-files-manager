{
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

    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
      };
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

  outputs = inputs@{ flake-parts, systems, ... }: flake-parts.lib.mkFlake { inherit inputs; } {
    systems = import systems;
    imports = [
      inputs.treefmt-nix.flakeModule
      inputs.pre-commit-hooks.flakeModule
    ];

    perSystem = { config, pkgs, system, lib, ... }: {
      _module.args.pkgs = import inputs.nixpkgs {
        inherit system;
        overlays = [ inputs.poetry2nix.overlays.default ];
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

        pre-commit =
          let
            gitExe = lib.getExe pkgs.git;
          in
          pkgs.mkShell {
            shellHook = ''
              ${config.pre-commit.installationScript}
            
              hooksPath=$(${gitExe} config --local core.hooksPath)
              if [ "$hooksPath" == "../.git/hooks" ]; then
                  ${gitExe} config --local core.hooksPath ".git/hooks"
                  echo "Replaced core.hooksPath with \".git/hooks\""
              fi
            '';
          };
      };

      treefmt.config = {
        projectRootFile = "pyproject.toml";
        flakeCheck = false;

        programs = {
          # Nix
          nixpkgs-fmt.enable = true;

          # Python
          black.enable = true;
          isort = {
            enable = true;
            profile = "black";
          };

          # Other
          prettier.enable = true;
        };
        settings.formatter = {
          black.options = [ "--line-length=120" ];
        };
      };

      pre-commit.settings = {
        rootSrc = lib.mkForce ../.;
        settings.treefmt.package = config.treefmt.build.wrapper;

        hooks = {
          deadnix.enable = true;
          statix.enable = true;

          treefmt.enable = true;
        };
      };
    };

  };
}
