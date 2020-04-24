# Change Log

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


[Unreleased]: https://github.com/python-poetry/poetry/compare/1.0.0a6...master
[1.0.0a6]: https://github.com/python-poetry/poetry/releases/tag/1.0.0a6
