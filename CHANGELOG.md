# Changelog

<sub>The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).</sub>

## [Unreleased]

#### Deprecated

- Usage of `__collection__` to customize the collection name. Prefer the `collection`
  Config option ([more details](https://art049.github.io/odmantic/modeling/#collection))

#### Added

- Integration with Pydantic `Config` class:

  - It's now possible to define custom `json_encoders` on the Models
  - Some other `Config` options provided by Pydantic are now available ([more
    details](https://art049.github.io/odmantic/modeling/#advanced-configuration))

- Support CPython 3.9 ([#32](https://github.com/art049/odmantic/pull/32) by
  [@art049](https://github.com/art049))

- Unpin pydantic to support 1.7.0 ([#29](https://github.com/art049/odmantic/pull/29) by
  [@art049](https://github.com/art049))

## [0.2.1] - 2020-10-25

#### Fixed

- Fix combined use of `skip` and `limit` with `engine.find` (#25 by @art049)

## [0.2.0] - 2020-10-25

#### Deprecated

- Deprecate `AIOEngineDependency` to prefer a global engine object, [more
  details](https://art049.github.io/odmantic/usage_fastapi/#building-the-engine) (#21 by
  @art049)

#### Added

- [Add sorting support](https://art049.github.io/odmantic/querying/#sorting) (#17 by @adriencaccia)
- Support motor 2.3.0 (#20 by @art049)

#### Fixed

- Fix FastAPI usage with References (#19 by @art049)

#### Docs

- Adding a CONTRIBUTING.md file to the root directory with link to docs (#8 by @sanders41)
- Raw Query Usage Documentation Fix (#10 by @adeelsohailahmed)
- Update Filtering to include Bitwise Operator Warning (#24 by @adeelsohailahmed)

## [0.1.0] - 2020-10-19

#### Initial Release

[0.1.0]: https://github.com/art049/odmantic/releases/tag/v0.1.0
[0.2.0]: https://github.com/art049/odmantic/compare/v0.1.0...v0.2.0
[0.2.1]: https://github.com/art049/odmantic/compare/v0.2.0...v0.2.1
[unreleased]: https://github.com/art049/odmantic/compare/v0.2.1...HEAD
