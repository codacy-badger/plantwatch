# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.0.10] - 2017-02-15
### Added
- plants
- README

### Changed
- blocks overview now shows the annual total production of the selected plants.
- blocks allows the user to switch not only to the detailed block, but to the plant as well. 

### Fixed
- some ui and ui consistency improvements
- some localization improvements

## [0.0.9e] - 2017-01-25
### Added
- deploy script to toggle settings.py.

### Changed
- eval() part has been rewritten.

### Removed
- every use of eval() has been removed.

### Security
- vulnerability to eval() threats fixed.

## [0.0.9d] - 2017-01-24
### Added
- option to search by operating state.
- option to search by chp.

### Changed
- plants fired by more than one energy source are now contained as well.

### Fixed
- search did not contain all plants.

## [0.0.9c] - 2017-01-21
### Added
- CHANGELOG
- option to choose the sort behavior from 'ascending' and 'descending'.
- option to search by federal state.
- table to display a summary

### Changed
- frist column of every table is now bold.
- slider does not automatically changes the search and now reacts to the 'change request' button.

### Removed
- some dead js code.

### Fixed
- tremendous ui improvements.
- changing the slider does not remove the choices in other options

## [0.0.9b] - 2017-01-16
### Added
- nuclear power plants.
- nav bar, impressium
- option to sort by 'initial operation' or 'power'
### Changed
- filter by energysource has been changed from js based to django form based.
### Removed
- lots of dead js code.