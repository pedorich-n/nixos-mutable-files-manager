## environment\.mutable-files

Manage mutable files anywhere on the file-system\.
Like ` environment.etc `, but with a wider scope\.

**Warning:** Be careful about what files you are modifying with this module\.  
It doesn’t have a way to backup files\.  
It overwrites the files on the File System without asking any questions\.  
It runs as root, so it can overwrite anything\.



*Type:*
attribute set of (submodule)



*Default:*
` { } `



*Example:*

```
environment.mutable-files = {
  "/opt/example/config.yml" = {
    source = ./config.yml;
    user = "nobody";
    group = "users";
    mode = "664";
  };
};

```



## environment\.mutable-files\.\<name>\.enable



Whether this mutable file should be generated\.



*Type:*
boolean



*Default:*
` true `



## environment\.mutable-files\.\<name>\.group



Group name or GID of created file\.



*Type:*
null or string



*Default:*
` null `



*Example:*
` "users" `



## environment\.mutable-files\.\<name>\.permissions



UNIX permission (octal) to apply to files



*Type:*
null or string



*Default:*
` null `



*Example:*
` "664" `



## environment\.mutable-files\.\<name>\.source



Path of the source file\.



*Type:*
path



## environment\.mutable-files\.\<name>\.target



Absolute path to the destination file/folder



*Type:*
string



*Default:*
` "Attribute's name" `



*Example:*
` "/opt/example/config.yml" `



## environment\.mutable-files\.\<name>\.user



User name or UID of created file\.



*Type:*
null or string



*Default:*
` null `



*Example:*
` "root" `


