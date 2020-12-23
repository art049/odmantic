# Changelog

<sub>The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).</sub>

## [Unreleased]

- Remove `bypass_document_validation` save option to avoid `Not Authorized` errors ([#85](https://github.com/art049/odmantic/pull/85) by [@Olegt0rr](https://github.com/Olegt0rr))

- ⬆️ Update fastapi requirement from >=0.61.1,<0.63.0 to >=0.61.1,<0.64.0 ([#84](https://github.com/art049/odmantic/pull/84) by [@dependabot[bot]](https://github.com/apps/dependabot))

## [0.3.2] - 2020-12-15

#### Added

- Fix embedded model field update ([#77](https://github.com/art049/odmantic/pull/77) by [@art049](https://github.com/art049))

- Fix `datetime` bson inheritance issue ([#78](https://github.com/art049/odmantic/pull/78) by [@Olegt0rr](https://github.com/Olegt0rr))

#### Internals

- Migrate to the updated prettier precommit hook ([#74](https://github.com/art049/odmantic/pull/74) by [@art049](https://github.com/art049))

- Fix tox dependency install ([#72](https://github.com/art049/odmantic/pull/72) by [@art049](https://github.com/art049))

- Update uvicorn requirement from ^0.12.1 to ^0.13.0 ([#67](https://github.com/art049/odmantic/pull/67) by [@dependabot[bot]](https://github.com/apps/dependabot))

- Update mypy requirement from ^0.782 to ^0.790 ([#48](https://github.com/art049/odmantic/pull/48) by [@dependabot[bot]](https://github.com/apps/dependabot-preview))

- Update importlib-metadata requirement from ^1.0 to >=1,<4 ([#54](https://github.com/art049/odmantic/pull/54) by [@dependabot[bot]](https://github.com/apps/dependabot))

- Update flake8 requirement from ==3.8.3 to ==3.8.4 ([#47](https://github.com/art049/odmantic/pull/47) by [@dependabot[bot]](https://github.com/apps/dependabot-preview))

- Update fastapi requirement from ^0.61.1 to >=0.61.1,<0.63.0 ([#59](https://github.com/art049/odmantic/pull/59) by [@dependabot[bot]](https://github.com/apps/dependabot))

## [0.3.1] - 2020-11-16

#### Added

- Add `schema_extra` config option ([#41](https://github.com/art049/odmantic/pull/41) by [@art049](https://github.com/art049))

#### Fixed

- Fix `setattr` error on a manually initialized EmbeddedModel ([#40](https://github.com/art049/odmantic/pull/40) by [@art049](https://github.com/art049))

## [0.3.0] - 2020-11-09

#### Deprecated

- Deprecate usage of `__collection__` to customize the collection name. Prefer the
  `collection` Config option ([more
  details](https://art049.github.io/odmantic/modeling/#collection))

#### Added

- Allow parsing document with unset fields defaults ([documentation](https://art049.github.io/odmantic/raw_query_usage/#advanced-parsing-behavior)) ([#28](https://github.com/art049/odmantic/pull/28) by [@art049](https://github.com/art049))

- Integration with Pydantic `Config` class ([#37](https://github.com/art049/odmantic/pull/37) by [@art049](https://github.com/art049)):

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
[0.3.0]: https://github.com/art049/odmantic/compare/v0.2.1...v0.3.0
[0.3.1]: https://github.com/art049/odmantic/compare/v0.3.0...v0.3.1
[0.3.2]: https://github.com/art049/odmantic/compare/v0.3.1...v0.3.2
[unreleased]: https://github.com/art049/odmantic/compare/v0.3.2...HEAD
