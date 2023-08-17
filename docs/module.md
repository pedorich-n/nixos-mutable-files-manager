## environment\.mutable-files

Manage mutable files anywhere on the file system\.
Like `environment.etc`, but with a broader scope\.

**Warning:** Exercise caution when modifying files using this module\.  
It does not have a backup mechanism for files\.  
The module overwrites files on the file system without prompting for confirmation\.  
As it runs with root privileges, it can overwrite anything\.

_Type:_
attribute set of (submodule)

_Default:_
`{ }`

_Example:_

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

Indicates whether this mutable file should be generated\.

_Type:_
boolean

_Default:_
`true`

## environment\.mutable-files\.\<name>\.group

Group name or GID of the created file\.  
This does not apply to intermediate folders\.  
If a folder needs to be created, it will be owned by `root`\.

_Type:_
null or string

_Default:_
`null`

_Example:_
`"users"`

## environment\.mutable-files\.\<name>\.permissions

UNIX permission (octal) to be applied to files\.  
This does not apply to intermediate folders\.  
If a folder needs to be created, it will have permissions `777`\.

_Type:_
null or string

_Default:_
`null`

_Example:_
`"664"`

## environment\.mutable-files\.\<name>\.source

Path to the source file\.

_Type:_
path

## environment\.mutable-files\.\<name>\.target

Absolute path to the destination file/folder\.

_Type:_
string

_Default:_
`"Attribute's name"`

_Example:_
`"/opt/example/config.yml"`

## environment\.mutable-files\.\<name>\.user

User name or UID of the created file\.  
This does not apply to intermediate folders\.  
If a folder needs to be created, it will be owned by `root`\.

_Type:_
null or string

_Default:_
`null`

_Example:_
`"root"`
