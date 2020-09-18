# Change Log

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


[Unreleased]: https://github.com/python-poetry/poetry/compare/1.0.0b1...master
[1.0.0b1]: https://github.com/python-poetry/poetry/releases/tag/1.0.0b1
[1.0.0a9]: https://github.com/python-poetry/poetry/releases/tag/1.0.0a9
[1.0.0a8]: https://github.com/python-poetry/poetry/releases/tag/1.0.0a8
[1.0.0a7]: https://github.com/python-poetry/poetry/releases/tag/1.0.0a7
[1.0.0a6]: https://github.com/python-poetry/poetry/releases/tag/1.0.0a6
