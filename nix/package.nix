{ pkgs }:
pkgs.poetry2nix.mkPoetryApplication {
  projectDir = ./..;
  checkGroups = [ ]; # To omit dev dependencies
  meta.mainProgram = "nixos-mutable-files-manager";
  overrides = pkgs.poetry2nix.overrides.withDefaults (_: prev: {
    expression = prev.expression.overridePythonAttrs (old: { buildInputs = (old.buildInputs or [ ]) ++ [ prev.poetry-core ]; });
  });
}
