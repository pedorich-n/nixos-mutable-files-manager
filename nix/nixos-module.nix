{ package, ... }:
{ pkgs, config, lib, ... }:
with lib;
let
  cfg = config.environment.mutable-files;

  filtered = with builtins; filter (entry: entry.enable) (attrValues cfg);

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

  modeType = with types; addCheck str (value: (builtins.match "^[0-7]{3,4}$" value) != null);

  mutableFileSubmodule = types.submodule ({ name, config, options, ... }: {
    options = {
      source = mkOption {
        type = types.path;
        description = lib.mdDoc ''
          Path to the source file.
        '';
      };

      enable = mkOption {
        type = types.bool;
        default = true;
        description = lib.mdDoc ''
          Indicates whether this mutable file should be generated.
        '';
      };

      target = mkOption {
        type = types.str;
        example = literalExpression ''"/opt/example/config.yml"'';
        defaultText = lib.mdDoc "Attribute's name";
        description = lib.mdDoc ''
          Absolute path to the destination file/folder.
        '';
      };

      user = mkOption {
        default = null;
        type = with types; nullOr str;
        example = "root";
        description = lib.mdDoc ''
          User name or UID of the created file.  
          This does not apply to intermediate folders.  
          If a folder needs to be created, it will be owned by `root`.
        '';
      };

      group = mkOption {
        default = null;
        type = with types; nullOr str;
        example = "users";
        description = lib.mdDoc ''
          Group name or GID of the created file.  
          This does not apply to intermediate folders.  
          If a folder needs to be created, it will be owned by `root`.
        '';
      };

      mode = mkOption {
        default = null;
        type = with types; nullOr modeType;
        example = "664";
        description = lib.mdDoc ''
          UNIX permission (octal) to be applied to files.  
          This does not apply to intermediate folders.  
          If a folder needs to be created, it will have permissions `777`.
        '';
      };

      # TODO: someday
      # backup = mkOption {
      #   type = types.bool;
      #   default = false;
      #   description = lib.mdDoc ''
      #     If enabled, all changed files will be backed up with ".bak" extension 
      #     before replacing them with new ones
      #   '';
      # };
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
      description = lib.mdDoc ''
        Manage mutable files anywhere on the file system.
        Like {option}`environment.etc`, but with a broader scope.

        ::: {.warning}
        Exercise caution when modifying files using this module.\
        It does not have a backup mechanism for files.\
        The module overwrites files on the file system without prompting for confirmation.\
        As it runs with root privileges, it can overwrite anything.
        :::
      '';
      example = literalExpression ''
        environment.mutable-files = {
          "/opt/example/config.yml" = {
            source = ./config.yml;
            user = "nobody";
            group = "users";
            mode = "664";
          };
        };
      '';
    };
  };

  ###### implementation
  config = mkIf (filtered != [ ]) {
    assertions = [{
      #TODO: better matcher. Filter out *, /../, /./
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
