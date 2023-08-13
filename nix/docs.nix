{ lib, pkgs }:
let
  moduleDoc = pkgs.nixosOptionsDoc {
    inherit ((lib.evalModules {
      modules = [
        ./nixos-module.nix
        { _module.check = false; }
      ];
    })) options;
  };

  # TODO: use passthru to have a separate command to serve docs?
  # See: https://github.com/nix-community/ethereum.nix/blob/main/mkdocs.nix#L76-L83
in
pkgs.runCommand "nixos-mutable-files-manager.doc"
{
  nativeBuildInputs = with pkgs; [ less glow ];
  meta.mainProgram = "showdocs.sh";
} ''
  mkdir -p $out/docs
  cp ${moduleDoc.optionsCommonMark} $out/docs/module.md

  mkdir -p $out/bin
  echo "${pkgs.glow}/bin/glow -p $out/docs/module.md" > $out/bin/showdocs.sh  
  chmod +x $out/bin/showdocs.sh
''
