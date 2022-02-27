# Change Log

## [1.0.8] - 2022-02-27

### Added

- Add hooks according to PEP-660 for editable installs ([#257](https://github.com/python-poetry/poetry-core/pull/257)).


## [1.0.7] - 2021-10-04

### Fixed

- Fixed an issue where the wrong `git` executable could be used on Windows. ([#213](https://github.com/python-poetry/poetry-core/pull/213))
- Fixed an issue where the Python 3.10 classifier was not automatically added. ([#215](https://github.com/python-poetry/poetry-core/pull/215))


## [1.0.6] - 2021-09-21

### Added

- Added support for more hash types gen generating hashes. ([#207](https://github.com/python-poetry/poetry-core/pull/207))


## [1.0.5] - 2021-09-18

### Fixed

- Fixed the copy of `Package` instances which led to file hashes not being available. ([#193](https://github.com/python-poetry/poetry-core/pull/193))
- Fixed an issue where unsafe parameters could be passed to `git` commands. ([#203](https://github.com/python-poetry/poetry-core/pull/203))
- Fixed an issue where the wrong `git` executable could be used on Windows. ([#205](https://github.com/python-poetry/poetry-core/pull/205))


## [1.0.4] - 2021-08-19

### Fixed

- Fixed an error in the way python markers with a precision >= 3 were handled. ([#180](https://github.com/python-poetry/poetry-core/pull/180))
- Fixed an error in the evaluation of `in/not in` markers ([#189](https://github.com/python-poetry/poetry-core/pull/189))


## [1.0.3] - 2021-04-09

### Fixed

- Fixed an error when handling single-digit Python markers ([#156](https://github.com/python-poetry/poetry-core/pull/156)).
- Fixed dependency markers not being properly copied when changing the constraint ([#163](https://github.com/python-poetry/poetry-core/pull/163)).


## [1.0.2] - 2021-02-05

### Fixed

- Fixed a missing import causing an error in Poetry ([#134](https://github.com/python-poetry/poetry-core/pull/134)).


## [1.0.1] - 2021-02-05

### Fixed

- Fixed PEP 508 representation of dependency without extras ([#102](https://github.com/python-poetry/poetry-core/pull/102)).
- Fixed an error where development dependencies were being resolved when invoking the PEP-517 backend ([#101](https://github.com/python-poetry/poetry-core/pull/101)).
- Fixed source distribution not being deterministic ([#105](https://github.com/python-poetry/poetry-core/pull/105)).
- Fixed an error where zip files were left open when building wheels ([#122](https://github.com/python-poetry/poetry-core/pull/122)).
- Fixed an error where explicitly included files were still not present in final distributions ([#124](https://github.com/python-poetry/poetry-core/pull/124)).
- Fixed wheel filename matching for recent architecture ([#125](https://github.com/python-poetry/poetry-core/pull/125), [#129](https://github.com/python-poetry/poetry-core/pull/129)).
- Fixed an error where the `&` character was not accepted for author names ([#120](https://github.com/python-poetry/poetry-core/pull/120)).
- Fixed the PEP-508 representation of some dependencies ([#103](https://github.com/python-poetry/poetry-core/pull/103)).
- Fixed the `Requires-Python` metadata generation ([#127](https://github.com/python-poetry/poetry-core/pull/127)).
- Fixed an error where pre-release versions were accepted in version constraints ([#128](https://github.com/python-poetry/poetry-core/pull/128)).


## [1.0.0] - 2020-09-30

No changes.


## [1.0.0rc3] - 2020-09-30

### Changed

- Removed `intreehooks` build backend in favor of the `backend-path` mechanism ([#90](https://github.com/python-poetry/poetry-core/pull/90)).
- Directory dependencies will now always use a posix path for their representation ([#90](https://github.com/python-poetry/poetry-core/pull/91)).
- Dependency constraints can now be set directly via a proper setter ([#90](https://github.com/python-poetry/poetry-core/pull/90)).


## [1.0.0rc2] - 2020-09-25

### Fixed

- Fixed `python_full_version` markers conversion to version constraints ([#86](https://github.com/python-poetry/core/pull/86)).


## [1.0.0rc1] - 2020-09-25

### Fixed

- Fixed Python constraint propagation when converting a package to a dependency ([#84](https://github.com/python-poetry/core/pull/84)).
- Fixed VCS ignored files being included in wheel distributions for projects using the `src` layout ([#81](https://github.com/python-poetry/core/pull/81))


## [1.0.0b1] - 2020-09-18

### Added

- Added support for build executable for wheels ([#72](https://github.com/python-poetry/core/pull/72)).

### Changed

- Improved packages with sources equality comparison ([#53](https://github.com/python-poetry/core/pull/53)).
- Improved licenses handling and packaging in builders ([#57](https://github.com/python-poetry/core/pull/57)).
- Refactored packages and dependencies classes to improve comparison between bare packages and packages with extras ([#78](https://github.com/python-poetry/core/pull/78)).

### Fixed

- Fixed PEP-508 representation of URL dependencies ([#60](https://github.com/python-poetry/core/pull/60)).
- Fixed generated `RECORD` files in some cases by ensuring it's a valid CSV file ([#61](https://github.com/python-poetry/core/pull/61)).
- Fixed an error when parsing some version constraints if they contained wildcard elements ([#56](https://github.com/python-poetry/core/pull/56)).
- Fixed errors when using the `exclude` property ([#62](https://github.com/python-poetry/core/pull/62)).
- Fixed the way git revisions are retrieved ([#69](https://github.com/python-poetry/core/pull/69)).
- Fixed dependency constraint PEP-508 compatibility when generating metadata ([#79](https://github.com/python-poetry/core/pull/79)).
- Fixed potential errors on Python 3.5 when building with the `include` property set ([#75](https://github.com/python-poetry/core/pull/75)).


## [1.0.0a9] - 2020-07-24

### Added

- Added support for build scripts without `setup.py` generation ([#45](https://github.com/python-poetry/core/pull/45)).

### Changed

- Improved the parsing of requirements and environment markers ([#44](https://github.com/python-poetry/core/pull/44)).

### Fixed

- Fixed the default value used for the `build.generate-setup-file` settings ([#43](https://github.com/python-poetry/core/pull/43)).
- Fixed error messages when the authors specified in the pyproject.toml file are invalid ([#49](https://github.com/python-poetry/core/pull/49)).
- Fixed distributions build when using the PEP-517 backend for packages with includes ([#47](https://github.com/python-poetry/core/pull/47)).


## [1.0.0a8] - 2020-06-26

### Fixed

- Fixed errors in the way Python environment markers were parsed and generated ([#36](https://github.com/python-poetry/core/pull/36)).


## [1.0.0a7] - 2020-05-06

### Added

- Added support for format-specific includes via the `include` property ([#6](https://github.com/python-poetry/core/pull/6)).

### Changed

- Allow url dependencies in multiple constraints dependencies ([#32](https://github.com/python-poetry/core/pull/32)).

### Fixed

- Fixed PEP 508 representation and parsing of VCS dependencies ([#30](https://github.com/python-poetry/core/pull/30)).


## [1.0.0a6] - 2020-04-24


### Added

- Added support for markers inverse ([#21](https://github.com/python-poetry/core/pull/21)).
- Added support for specifying that `git` dependencies should be installed in develop mode ([#23](https://github.com/python-poetry/core/pull/23)).
- Added the ability to specify build settings from the Poetry main configuration file ([#26](https://github.com/python-poetry/core/pull/26)).
- Added the ability to disable the generation of the `setup.py` file when building ([#26](https://github.com/python-poetry/core/pull/26)).

### Changed

- Relaxed licence restrictions to support custom licences ([#5](https://github.com/python-poetry/core/pull/5)).
- Improved support for PEP-440 direct references ([#22](https://github.com/python-poetry/core/pull/22)).
- Improved dependency vendoring ([#25](https://github.com/python-poetry/core/pull/25)).

### Fixed

- Fixed the inability to make the url dependencies optional ([#13](https://github.com/python-poetry/core/pull/13)).
- Fixed whitespaces in PEP-440 constraints causing an error ([#16](https://github.com/python-poetry/core/pull/16)).
- Fixed subpackage check when generating the `setup.py` file ([#17](https://github.com/python-poetry/core/pull/17)).
- Fix PEP-517 issues for projects using build scripts ([#12](https://github.com/python-poetry/core/pull/12)).
- Fixed support for stub-only packages ([#28](https://github.com/python-poetry/core/pull/28)).


[Unreleased]: https://github.com/python-poetry/poetry-core/compare/1.0.8...1.0
[1.0.8]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.8
[1.0.7]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.7
[1.0.6]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.6
[1.0.5]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.5
[1.0.4]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.4
[1.0.3]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.3
[1.0.2]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.2
[1.0.1]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.1
[1.0.0]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.0
[1.0.0rc3]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.0rc3
[1.0.0rc2]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.0rc2
[1.0.0rc1]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.0rc1
[1.0.0b1]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.0b1
[1.0.0a9]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.0a9
[1.0.0a8]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.0a8
[1.0.0a7]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.0a7
[1.0.0a6]: https://github.com/python-poetry/poetry-core/releases/tag/1.0.0a6
