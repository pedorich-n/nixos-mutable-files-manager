{ pkgs, config, lib, ... }:
with lib;
let
  cfg = config.environment.mutable-files;

  filtered = with builtins; filter (entry: entry.enable) (attrValues cfg);
  enabled = filtered != [ ];

  package = pkgs.callPackage ./package.nix { };

  mutableFilesStore = pkgs.runCommandLocal "mutable-files" { } ''
    set -euo pipefail

    makeEntry() {
      src="$1"
      target="$2"
      mode="$3"
      user="$4"
      group="$5"

      files="$out/files/"
      metadata="$out/metadata/"

      dir=$(dirname "$target")
      mkdir -p "$files/$dir"
      mkdir -p "$metadata/$dir"

      if ! [ -e "$files/$target" ]; then
        ln -s "$src" "$files/$target"
      else
        echo "duplicate entry $target -> $src"
        if [ "$(readlink "$files/$target")" != "$src" ]; then
          echo "mismatched duplicate entry $(readlink "$files/$target") <-> $src"
          ret=1

          continue
        fi
      fi

      ${getExe pkgs.jq} -n \
        --arg usr "$user" \
        --arg grp "$group" \
        --arg md "$mode" \
        '{user: $usr, group: $grp, mode: $md}' > "$metadata/$target.meta"
    }

    mkdir -p "$out"

    ${concatMapStringsSep "\n" (entry: escapeShellArgs [
      "makeEntry"
      "${entry.source}"
      entry.target
      entry.mode
      entry.user
      entry.group
    ]) filtered }
  '';

  mutableFileSubmodule = types.submodule ({ name, config, options, ... }: {
    options = {
      source = mkOption {
        type = types.path;
        description = lib.mdDoc "Path of the source file or folder";
      };

      enable = mkOption {
        type = types.bool;
        default = true;
        description = lib.mdDoc ''
          Whether this mutable file should be generated.
        '';
      };

      target = mkOption {
        type = types.str;
        description = lib.mdDoc ''
          Absolute path to the destination file/folder
        '';
      };

      user = mkOption {
        default = null;
        type = with types; nullOr str;
        description = lib.mdDoc ''
          User name or UID of created file.
        '';
      };

      group = mkOption {
        default = null;
        type = with types; nullOr str;
        description = lib.mdDoc ''
          Group name or GID of created file.
        '';
      };

      mode = mkOption {
        default = null;
        type = with types; nullOr str; #TODO: custom type with validation?
        example = "664";
        description = lib.mdDoc ''
          UNIX mode to apply to created files
        '';
      };

      backup = mkOption {
        type = types.bool;
        default = false;
        description = lib.mdDoc ''
          If enabled, all changed files will be backed up with ".bak" extension 
          before replacing them with new ones
        '';
      };

      verbose = mkOption {
        type = types.bool;
        default = false;
        description = lib.mdDoc ''
          Whether to enable verbose logging for this file/folder
        '';
      };
    };

    config = {
      target = mkDefault name;
    };
  });

in
{
  ###### interface
  options = {
    environment.mutable-files = mkOption {
      type = types.attrsOf mutableFileSubmodule;
      default = { };
      description = lib.mdDoc "TODO";
    };
  };

  ###### implementation
  config = mkIf enabled {
    assertions = [{
      #TODO: better matcher. Filter out *, /../, /./, etc
      assertion = builtins.all (entry: (strings.hasPrefix "/" entry.target)) filtered;
      message = "Paths must be absolute and full!";
    }];

    systemd.services.mutable-files = {
      description = "Manage mutable files with NixOS module";
      wantedBy = [ "multi-user.target" ];

      script = ''
        ${getExe package} \
          --source "${mutableFilesStore}/files" \
          --metadata "${mutableFilesStore}/metadata" \
          --destination "/" \
          --state "/var/lib/mutable-files/state.txt"
      '';

      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        StateDirectory = "mutable-files";
      };
    };
  };
}
