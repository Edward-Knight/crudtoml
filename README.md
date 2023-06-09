# [crudtoml](https://github.com/Edward-Knight/crudtoml)

[![PyPI - Status](https://img.shields.io/pypi/status/crudtoml)](https://pypi.org/project/crudtoml/)
[![PyPI - License](https://img.shields.io/pypi/l/crudtoml)](https://pypi.org/project/crudtoml/)
[![PyPI - Latest Project Version](https://img.shields.io/pypi/v/crudtoml)](https://pypi.org/project/crudtoml/)

Perform CRUD operations on TOML files.


## Features

* Style-preserving edits
* Supports indexing into arrays
* Write back to input file with `-i`
* "Shell-compatible" output à la `jq` with `-r`


## Examples

```shell
$ echo -e '[project]\nname = "crudtoml"' | tee test.toml
[project]
name = "crudtoml"
```

### Create!

```shell
$ crudtoml test.toml create project dob 2023-05-23
[project]
name = "crudtoml"
dob = 2023-06-23
```

### Read!

```shell
$ crudtoml test.toml read project name
"crudtoml"
```

### Update!

```shell
$ crudtoml test.toml update project name '"crudini"'
[project]
name = "crudini"
```

### Delete!

```shell
$ crudtoml test.toml delete project name
[project]
```
