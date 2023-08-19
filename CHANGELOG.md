# Change Log


## [1.7.0] - 2023-08-20

### Added

- Optionally use resolved references when converting a VCS dependency to a PEP 508 dependency specification ([#603](https://github.com/python-poetry/poetry-core/pull/603)).
- Improve performance of marker handling ([#609](https://github.com/python-poetry/poetry-core/pull/609)).

### Changed

- Drop support for Python 3.7 ([#566](https://github.com/python-poetry/poetry-core/pull/566)).
- Remove deprecated `poetry.core.constraints.generic` and `poetry.core.semver` ([#601](https://github.com/python-poetry/poetry-core/pull/601)).
- Allow `|` as a value separator in markers with the operators `in` and `not in` ([#608](https://github.com/python-poetry/poetry-core/pull/608)).
- Put pretty name (instead of normalized name) in metadata ([#620](https://github.com/python-poetry/poetry-core/pull/620)).
- Update list of supported licenses ([#623](https://github.com/python-poetry/poetry-core/pull/623)).

### Fixed

- Fix an issue where the encoding was not handled correctly when calling a subprocess ([#602](https://github.com/python-poetry/poetry-core/pull/602)).
- Fix an issue where caret constraints with additional whitespace could not be parsed ([#606](https://github.com/python-poetry/poetry-core/pull/606)).
- Fix an issue where PEP 508 dependency specifications with names starting with a digit could not be parsed ([#607](https://github.com/python-poetry/poetry-core/pull/607)).
- Fix an issue where Poetry considered an unrelated `.gitignore` file resulting in an empty wheel ([#611](https://github.com/python-poetry/poetry-core/pull/611)).

### Vendoring

- [`lark==1.1.7`](https://github.com/lark-parser/lark/releases/tag/1.1.7)


## [1.6.1] - 2023-05-29

### Fixed

- Fix an endless recursion in marker handling ([#593](https://github.com/python-poetry/poetry-core/pull/593)).
- Fix an issue where the wheel tag was not built correctly under certain circumstances ([#591](https://github.com/python-poetry/poetry-core/pull/591)).
- Fix an issue where the tests included in the sdist failed due to missing files ([#589](https://github.com/python-poetry/poetry-core/pull/589)).


## [1.6.0] - 2023-05-14

### Added

- Improve error message for invalid markers ([#569](https://github.com/python-poetry/poetry-core/pull/569)).
- Increase robustness when deleting temporary directories on Windows ([#460](https://github.com/python-poetry/poetry-core/pull/460)).
- Add support for file dependencies with subdirectories ([#467](https://github.com/python-poetry/poetry-core/pull/467)).

### Changed

- Replace `tomlkit` with `tomli`, which changes the interface of some _internal_ classes ([#483](https://github.com/python-poetry/poetry-core/pull/483)).
- Deprecate `Package.category` ([#561](https://github.com/python-poetry/poetry-core/pull/561)).

### Fixed

- Fix a performance regression in marker handling ([#568](https://github.com/python-poetry/poetry-core/pull/568)).
- Fix an issue where wildcard version constraints were not handled correctly ([#402](https://github.com/python-poetry/poetry-core/pull/402)).
- Fix an issue where `poetry build` created duplicate Python classifiers if they were specified manually ([#578](https://github.com/python-poetry/poetry-core/pull/578)).
- Fix an issue where local versions where not handled correctly ([#579](https://github.com/python-poetry/poetry-core/pull/579)).

### Vendoring

- [`attrs==23.1.0`](https://github.com/python-attrs/attrs/blob/main/CHANGELOG.md)
- [`packaging==23.1`](https://github.com/pypa/packaging/blob/main/CHANGELOG.rst)
- [`tomli==2.0.1`](https://github.com/hukkin/tomli/blob/master/CHANGELOG.md)
- [`typing-extensions==4.5.0`](https://github.com/python/typing_extensions/blob/main/CHANGELOG.md)


## [1.5.2] - 2023-03-13

### Fixed

- Fix an issue where wheels built on Windows could contain duplicate entries in the RECORD file ([#555](https://github.com/python-poetry/poetry-core/pull/555)).


## [1.5.1] - 2023-02-20

### Changed

- Improve performance by caching parsed markers, constraints and versions ([#556](https://github.com/python-poetry/poetry-core/pull/556)).


## [1.5.0] - 2023-01-27

### Added

- Improve marker handling ([#528](https://github.com/python-poetry/poetry-core/pull/528),
[#534](https://github.com/python-poetry/poetry-core/pull/534),
[#530](https://github.com/python-poetry/poetry-core/pull/530),
[#546](https://github.com/python-poetry/poetry-core/pull/546),
[#547](https://github.com/python-poetry/poetry-core/pull/547)).
- Allow overriding the output directory when building dist files ([#527](https://github.com/python-poetry/poetry-core/pull/527)).
- Validate whether dependencies referenced in `extras` are defined in the main dependency group ([#542](https://github.com/python-poetry/poetry-core/pull/542)).
- Improve handling of generic constraints ([#515](https://github.com/python-poetry/poetry-core/pull/515)).

### Changed

- Deprecate the hash function of `FileDependency` ([#535](https://github.com/python-poetry/poetry-core/pull/535)).
- Do not set `allows_preleases` implicitly anymore if the lower bound of a constraint is a pre-release ([#543](https://github.com/python-poetry/poetry-core/pull/543)).
- Poetry no longer generates a `setup.py` file in sdists by default ([#318](https://github.com/python-poetry/poetry-core/pull/318)).
- Remove the unused `platform` attribute from `Package` ([#548](https://github.com/python-poetry/poetry-core/pull/548)).
- Deprecate the `pretty_version` parameter when creating a `Package` ([#549](https://github.com/python-poetry/poetry-core/pull/549)).
- Validate path dependencies during use instead of during construction ([#520](https://github.com/python-poetry/poetry-core/pull/520)).

### Fixed

- Fix an issue where the PEP 517 `metadata_directory` was not respected when building an editable wheel ([#537](https://github.com/python-poetry/poetry-core/pull/537)).
- Fix an issue where trailing newlines were allowed in `tool.poetry.description` ([#505](https://github.com/python-poetry/poetry-core/pull/505)).
- Fix an issue where the name of the data folder in wheels was not normalized ([#532](https://github.com/python-poetry/poetry-core/pull/532)).
- Fix an issue where the order of entries in the RECORD file was not deterministic ([#545](https://github.com/python-poetry/poetry-core/pull/545)).
- Fix an issue where parsing of VCS URLs with escaped characters failed ([#524](https://github.com/python-poetry/poetry-core/pull/524)).
- Fix an issue where the subdirectory parameter of VCS URLs was not respected ([#518](https://github.com/python-poetry/poetry-core/pull/518)).
- Fix an issue where zero padding was not correctly handled in version comparisons ([#540](https://github.com/python-poetry/poetry-core/pull/540)).
- Fix an issue where sdist builds did not support multiple READMEs ([#486](https://github.com/python-poetry/poetry-core/pull/486)).

### Vendoring

- [`attrs==22.2.0`](https://github.com/python-attrs/attrs/blob/main/CHANGELOG.md)
- [`jsonschema==4.17.3`](https://github.com/python-jsonschema/jsonschema/blob/main/CHANGELOG.rst)
- [`lark==1.1.5`](https://github.com/lark-parser/lark/releases/tag/1.1.5)
- [`packaging==23.0`](https://github.com/pypa/packaging/blob/main/CHANGELOG.rst)
- [`pyrsistent==0.19.3`](https://github.com/tobgu/pyrsistent/blob/master/CHANGES.txt)


## [1.4.0] - 2022-11-22

### Added

- The PEP 517 `metadata_directory` is now respected as an input to the `build_wheel` hook ([#487](https://github.com/python-poetry/poetry-core/pull/487)).

### Changed

- Sources are now considered more carefully when dealing with dependencies with environment markers ([#497](https://github.com/python-poetry/poetry-core/pull/497)).
- `EmptyConstraint` is now hashable ([#513](https://github.com/python-poetry/poetry-core/pull/513)).
- `ParseConstraintError` is now raised on version and constraint parsing errors, and includes information on the package that caused the error ([#514](https://github.com/python-poetry/poetry-core/pull/514)).

### Fixed

- Fix an issue where invalid PEP 508 requirements were generated due to a missing space before semicolons ([#510](https://github.com/python-poetry/poetry-core/pull/510)).
- Fix an issue where relative paths were encoded into package requirements, instead of a file:// URL as required by PEP 508 ([#512](https://github.com/python-poetry/poetry-core/pull/512)).

### Vendoring

- [`jsonschema==4.17.0`](https://github.com/python-jsonschema/jsonschema/blob/main/CHANGELOG.rst)
- [`lark==1.1.4`](https://github.com/lark-parser/lark/releases/tag/1.1.4)
- [`pyrsistent==0.19.2`](https://github.com/tobgu/pyrsistent/blob/master/CHANGES.txt)
- [`tomlkit==0.11.6`](https://github.com/sdispater/tomlkit/blob/master/CHANGELOG.md)
- [`typing-extensions==4.4.0`](https://github.com/python/typing_extensions/blob/main/CHANGELOG.md)


## [1.3.2] - 2022-10-07

### Fixed

- Fix an issue where the normalization was not applied to the path of an sdist built using a PEP 517 frontend ([#495](https://github.com/python-poetry/poetry-core/pull/495)).


## [1.3.1] - 2022-10-05

### Fixed

- Fix an issue where a typing-driven assertion could be false at runtime, causing a failure during prepare_metadata_for_build_wheel ([#492](https://github.com/python-poetry/poetry-core/pull/492)).


## [1.3.0] - 2022-10-05

### Added

- Add `3.11` to the list of available Python versions ([#477](https://github.com/python-poetry/poetry-core/pull/477)).

### Changed

- Deprecate `poetry.core.constraints.generic`, which is replaced by `poetry.core.packages.constraints` ([#482](https://github.com/python-poetry/poetry-core/pull/482)).
- Deprecate `poetry.core.semver`, which is replaced by `poetry.core.constraints.version` ([#482](https://github.com/python-poetry/poetry-core/pull/482)).

### Fixed

- Fix an issue where versions were escaped wrongly when building the wheel name ([#469](https://github.com/python-poetry/poetry-core/pull/469)).
- Fix an issue where caret constraints of pre-releases with a major version of 0 resulted in an empty version range ([#475](https://github.com/python-poetry/poetry-core/pull/475)).
- Fix an issue where the names of extras were not normalized according to PEP 685 ([#476](https://github.com/python-poetry/poetry-core/pull/476)).
- Fix an issue where sdist names were not normalized ([#484](https://github.com/python-poetry/poetry-core/pull/484)).


## [1.2.0] - 2022-09-13

### Added

- Added support for subdirectories in `url` dependencies  ([#398](https://github.com/python-poetry/poetry-core/pull/398)).

### Changed

- When setting an invalid version constraint an error is raised instead of silently setting "any version" ([#461](https://github.com/python-poetry/poetry-core/pull/461)).
- Allow more characters in author name ([#411](https://github.com/python-poetry/poetry-core/pull/411)).

### Fixed

- Fixed an issue where incorrect `Requires-Dist` information was generated when environment markers where used for optional packages ([#462](https://github.com/python-poetry/poetry-core/pull/462)).
- Fixed an issue where incorrect python constraints were parsed from environment markers ([#457](https://github.com/python-poetry/poetry-core/pull/457)).
- Fixed the hashing of markers and constraints ([#466](https://github.com/python-poetry/poetry-core/pull/466)).
- Fixed an issue where the PEP 508 name of directory dependencies used platform paths ([#463](https://github.com/python-poetry/poetry-core/pull/463)).


## [1.1.0] - 2022-08-31

- No functional changes.


## [1.1.0rc3] - 2022-08-26

### Fixed

- Fixed an issue where a malformed URL was passed to pip when installing from a git subdirectory ([#451](https://github.com/python-poetry/poetry-core/pull/451)).


## [1.1.0rc2] - 2022-08-26

### Changed

- Enabled setting `version` of `ProjectPackage` to support dynamically setting the project's package version (e.g. from a plugin) ([#447](https://github.com/python-poetry/poetry-core/pull/447)).

### Fixed

- Fixed an issue where `authors` property was not detected ([#437](https://github.com/python-poetry/poetry-core/pull/437)).
- Fixed an issue where submodules of git dependencies was not checked out ([#439](https://github.com/python-poetry/poetry-core/pull/439)).
- Fixed an issue with Python constraints from markers ([#448](https://github.com/python-poetry/poetry-core/pull/448)).
- Fixed an issue where the latest version of git dependency was selected instead of the locked one ([#449](https://github.com/python-poetry/poetry-core/pull/449)).


## [1.1.0rc1] - 2022-08-17

### Changed

- Replaced Poetry's helper method `canonicalize_name()` by `packaging.utils.canonicalize_name()` ([#418](https://github.com/python-poetry/poetry-core/pull/418)).
- Removed unused code ([#419](https://github.com/python-poetry/poetry-core/pull/419)).

### Fixed

- Fixed an issue with markers, that results in incorrectly resolved extra dependencies ([#415](https://github.com/python-poetry/poetry-core/pull/415)).
- Fixed an issue where equal markers had not the same hash ([#417](https://github.com/python-poetry/poetry-core/pull/417)).
- Fixed `allows_any()` for local versions ([#433](https://github.com/python-poetry/poetry-core/pull/433)).
- Fixed special cases of `next_major()`, `next_minor()`, etc. and deprecated ambiguous usage ([#434](https://github.com/python-poetry/poetry-core/pull/434)).
- Fixed an issue with Python constraints from markers ([#436](https://github.com/python-poetry/poetry-core/pull/436)).


## [1.1.0b3] - 2022-07-09

### Added

- Added support for valid PEP 517 projects with another build-system than poetry-core as directory dependencies  ([#368](https://github.com/python-poetry/poetry-core/pull/368), [#377](https://github.com/python-poetry/poetry-core/pull/377)).
- Added support for yanked files and releases according to PEP 592 ([#400](https://github.com/python-poetry/poetry-core/pull/400)).

### Changed

- Relaxed schema validation to allow additional properties ([#369](https://github.com/python-poetry/poetry-core/pull/369)).
- Harmonized string representation of dependencies ([#393](https://github.com/python-poetry/poetry-core/pull/393)).
- Changed wheel name normalization to follow most recent packaging specification ([#394](https://github.com/python-poetry/poetry-core/pull/394)).
- Changed equality check of direct origin dependencies, so that constraints are not considered anymore ([#405](https://github.com/python-poetry/poetry-core/pull/405)).
- Deprecated `Dependency.set_constraint()` and replaced it by a `constraint` property for consistency ([#370](https://github.com/python-poetry/poetry-core/pull/370)).
- Removed `Package.requires_extras` ([#374](https://github.com/python-poetry/poetry-core/pull/374)).
- Improved marker handling ([#380](https://github.com/python-poetry/poetry-core/pull/380),
[#383](https://github.com/python-poetry/poetry-core/pull/383),
[#384](https://github.com/python-poetry/poetry-core/pull/384),
[#390](https://github.com/python-poetry/poetry-core/pull/390),
[#395](https://github.com/python-poetry/poetry-core/pull/395)).

### Fixed

- Fixed hash method for `PackageSpecification`, `Package`, `Dependency` and their sub classes ([#370](https://github.com/python-poetry/poetry-core/pull/370)).
- Fixed merging of markers `python_version` and `python_full_version` ([#382](https://github.com/python-poetry/poetry-core/pull/382), [#388](https://github.com/python-poetry/poetry-core/pull/388)).
- Fixed python version normalization ([#385](https://github.com/python-poetry/poetry-core/pull/385), [#407](https://github.com/python-poetry/poetry-core/pull/407)).
- Fixed an issue where version identifiers with a local version segment allowed non local versions ([#396](https://github.com/python-poetry/poetry-core/pull/396)).
- Fixed an issue where version identifiers without a post release segment allowed post releases ([#396](https://github.com/python-poetry/poetry-core/pull/396)).
- Fixed script definitions that didn't work when extras were not explicitly defined ([#404](https://github.com/python-poetry/poetry-core/pull/404)).


## [1.1.0b2] - 2022-05-24

### Fixed

- Fixed a regression where `poetry-core` no longer handled improper Python version constraints from package metadata ([#371](https://github.com/python-poetry/poetry-core/pull/371))
- Fixed missing version bump in `poetry.core.__version__` ([#367](https://github.com/python-poetry/poetry-core/pull/367))

### Improvements

- `poetry-core` generated wheel's now correctly identify `Generator` metadata as `poetry-core` instead of `poetry` ([#367](https://github.com/python-poetry/poetry-core/pull/367))


## [1.1.0b1] - 2022-05-23

### Fixed

- Fixed an issue where canonicalize package names leads to infinite loops ([#328](https://github.com/python-poetry/poetry-core/pull/328)).
- Fixed an issue where versions wasn't correct normalized to PEP-440 ([#344](https://github.com/python-poetry/poetry-core/pull/344)).
- Fixed an issue with union of multi markers if one marker is a subset of the other marker ([#352](https://github.com/python-poetry/poetry-core/pull/352)).
- Fixed an issue with markers which are not in disjunctive normal form (DNF) ([#347](https://github.com/python-poetry/poetry-core/pull/347)).
- Fixed an issue where stub-only partial namespace packages were not recognized as packages ([#221](https://github.com/python-poetry/poetry-core/pull/221)).
- Fixed an issue where PEP-508 url requirements with extras were not parsed correctly ([#345](https://github.com/python-poetry/poetry-core/pull/345)).
- Fixed an issue where PEP-508 strings with wildcard exclusion constraints were incorrectly exported ([#343](https://github.com/python-poetry/poetry-core/pull/343)).
- Allow hidden directories on Windows bare repos ([#341](https://github.com/python-poetry/poetry-core/pull/341)).
- Fixed an issue where dependencies with an epoch are parsed as empty ([#316](https://github.com/python-poetry/poetry-core/pull/316)).
- Fixed an issue where a package consisting of multiple packages wasn't build correctly ([#292](https://github.com/python-poetry/poetry-core/pull/292)).

### Added

- Added support for handling git urls with subdirectory ([#288](https://github.com/python-poetry/poetry-core/pull/288)).
- Added support for metadata files as described in PEP-658 for PEP-503 "simple" API repositories ([#333](https://github.com/python-poetry/poetry-core/pull/333)).

### Changed

- Renamed dependency group of runtime dependencies to from `default` to `main` ([#326](https://github.com/python-poetry/poetry-core/pull/326)).

### Improvements

- `poetry-core` is now completely type checked.
- Improved the SemVer constraint parsing ([#327](https://github.com/python-poetry/poetry-core/pull/327)).
- Improved the speed when cloning git repositories ([#290](https://github.com/python-poetry/poetry-core/pull/290)).


## [1.1.0a7] - 2022-03-05

### Fixed

- Fixed an issue when evaluate `in/not in` markers ([#188](https://github.com/python-poetry/poetry-core/pull/188)).
- Fixed an issue when parsing of caret constraint with leading zero ([#201](https://github.com/python-poetry/poetry-core/pull/201)).
- Respect format for explicit included files when finding excluded files ([#228](https://github.com/python-poetry/poetry-core/pull/228)).
- Fixed an issue where only the last location was used when multiple packages should be included ([#108](https://github.com/python-poetry/poetry-core/pull/108)).
- Ensure that package `description` contains no new line ([#219](https://github.com/python-poetry/poetry-core/pull/219)).
- Fixed an issue where all default dependencies were removed instead of just the selected one ([#220](https://github.com/python-poetry/poetry-core/pull/220)).
- Ensure that authors and maintainers are normalized ([#276](https://github.com/python-poetry/poetry-core/pull/276)).

### Added

- Add support for most of the guaranteed hashes ([#207](https://github.com/python-poetry/poetry-core/pull/207)).
- Add support to declare multiple README files ([#248](https://github.com/python-poetry/poetry-core/pull/248)).
- Add support for git sub directories ([#192](https://github.com/python-poetry/poetry-core/pull/192)).
- Add hooks according to PEP-660 for editable installs ([#182](https://github.com/python-poetry/poetry-core/pull/182)).
- Add support for version epochs ([#264](https://github.com/python-poetry/poetry-core/pull/264)).

### Changed

- Drop python3.6 support ([#263](https://github.com/python-poetry/poetry-core/pull/263)).
- Loose the strictness when parsing version constraint to support invalid use of wildcards, e.g. `>=3.*` ([#186](https://github.com/python-poetry/poetry-core/pull/186)).
- No longer assume a default git branch name ([#192](https://github.com/python-poetry/poetry-core/pull/192)).
- Sort package name in extras to make it reproducible ([#280](https://github.com/python-poetry/poetry-core/pull/280)).

### Improvements

- Improve marker handling ([#208](https://github.com/python-poetry/poetry-core/pull/208),
[#282](https://github.com/python-poetry/poetry-core/pull/282),
[#283](https://github.com/python-poetry/poetry-core/pull/283),
[#284](https://github.com/python-poetry/poetry-core/pull/284),
[#286](https://github.com/python-poetry/poetry-core/pull/286),
[#291](https://github.com/python-poetry/poetry-core/pull/291),
[#293](https://github.com/python-poetry/poetry-core/pull/293),
[#294](https://github.com/python-poetry/poetry-core/pull/294),
[#297](https://github.com/python-poetry/poetry-core/pull/297)).


## [1.1.0a6] - 2021-07-30

### Added

- Added support for dependency groups. ([#183](https://github.com/python-poetry/poetry-core/pull/183))


## [1.1.0a5] - 2021-05-21

### Added

- Added support for script files in addition to standard entry points. ([#40](https://github.com/python-poetry/poetry-core/pull/40))

### Fixed

- Fixed an error in the way python markers with a precision >= 3 were handled. ([#178](https://github.com/python-poetry/poetry-core/pull/178))


## [1.1.0a4] - 2021-04-30

### Changed

- Files in source distributions now have a deterministic time to improve reproducibility. ([#142](https://github.com/python-poetry/poetry-core/pull/142))

### Fixed

- Fixed an error where leading zeros in the local build part of version specifications were discarded. ([#167](https://github.com/python-poetry/poetry-core/pull/167))
- Fixed the PEP 508 representation of file dependencies. ([#153](https://github.com/python-poetry/poetry-core/pull/153))
- Fixed the copy of `Package` instances which led to file hashes not being available. ([#159](https://github.com/python-poetry/poetry-core/pull/159))
- Fixed an error in the parsing of caret requirements with a pre-release lower bound. ([#171](https://github.com/python-poetry/poetry-core/pull/171))
- Fixed an error where some pre-release versions were not flagged as pre-releases. ([#170](https://github.com/python-poetry/poetry-core/pull/170))


## [1.1.0a3] - 2021-04-09

### Fixed

- Fixed dependency markers not being properly copied when changing the constraint ([#162](https://github.com/python-poetry/poetry-core/pull/162)).


## [1.1.0a2] - 2021-04-08

### Fixed

- Fixed performance regressions when parsing version constraints ([#152](https://github.com/python-poetry/poetry-core/pull/152)).
- Fixed how local build versions are handled and compared ([#157](https://github.com/python-poetry/poetry-core/pull/157), [#158](https://github.com/python-poetry/poetry-core/pull/158)).
- Fixed errors when parsing some environment markers ([#155](https://github.com/python-poetry/poetry-core/pull/155)).


## [1.1.0a1] - 2021-03-30

This version is the first to drop support for Python 2.7 and 3.5.

If you are still using these versions you should update the `requires` property of the `build-system` section
to restrict the version of `poetry-core`:

```toml
[build-system]
requires = ["poetry-core<1.1.0"]
build-backend = "poetry.core.masonry.api"
```

### Changed

- Dropped support for Python 2.7 and 3.5 ([#131](https://github.com/python-poetry/poetry-core/pull/131)).
- Reorganized imports internally to improve performances ([#131](https://github.com/python-poetry/poetry-core/pull/131)).
- Directory dependencies are now in non-develop mode by default ([#98](https://github.com/python-poetry/poetry-core/pull/98)).
- Improved support for PEP 440 specific versions that do not abide by semantic versioning ([#140](https://github.com/python-poetry/poetry-core/pull/140)).

### Fixed

- Fixed path dependencies PEP 508 representation ([#141](https://github.com/python-poetry/poetry-core/pull/141)).


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


[Unreleased]: https://github.com/python-poetry/poetry-core/compare/1.7.0...main
[1.7.0]: https://github.com/python-poetry/poetry-core/releases/tag/1.7.0
[1.6.1]: https://github.com/python-poetry/poetry-core/releases/tag/1.6.1
[1.6.0]: https://github.com/python-poetry/poetry-core/releases/tag/1.6.0
[1.5.2]: https://github.com/python-poetry/poetry-core/releases/tag/1.5.2
[1.5.1]: https://github.com/python-poetry/poetry-core/releases/tag/1.5.1
[1.5.0]: https://github.com/python-poetry/poetry-core/releases/tag/1.5.0
[1.4.0]: https://github.com/python-poetry/poetry-core/releases/tag/1.4.0
[1.3.2]: https://github.com/python-poetry/poetry-core/releases/tag/1.3.2
[1.3.1]: https://github.com/python-poetry/poetry-core/releases/tag/1.3.1
[1.3.0]: https://github.com/python-poetry/poetry-core/releases/tag/1.3.0
[1.2.0]: https://github.com/python-poetry/poetry-core/releases/tag/1.2.0
[1.1.0]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0
[1.1.0rc3]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0rc3
[1.1.0rc2]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0rc2
[1.1.0rc1]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0rc1
[1.1.0b3]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0b3
[1.1.0b2]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0b2
[1.1.0b1]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0b1
[1.1.0a7]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0a7
[1.1.0a6]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0a6
[1.1.0a5]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0a5
[1.1.0a4]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0a4
[1.1.0a3]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0a3
[1.1.0a2]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0a2
[1.1.0a1]: https://github.com/python-poetry/poetry-core/releases/tag/1.1.0a1
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
