# Changelog

All notable changes to this project will be documented in this file.
Changes are only recorded from 0.2.0 when the project was forked from the archived upstream project.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2021-03-08

### Added

- Support for a fixed-rate tariff for easy comparison with the Agile tariff.
- Unit tests.

### Changed

- Renamed the project to OctoCostToo after forking.
- Many of the original configuration options have been renamed to use snake_case.
- Gas usage used to determine the cost in £ per kWh is converted from m3 to kWh using the formula: `X × 1.02264 × 39.0 ÷ 3.6` or simply `X × 11.0786`.

### Fixed

- Standing charge for gas costing is now included in the cost calculations.

[Unreleased]: https://github.com/lildude/OctoCostToo/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/lildude/OctoCostToo/compare/v0.1.9...v0.2.0
