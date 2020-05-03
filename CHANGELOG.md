# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2020-05-01

### Added

- [#53](https://github.com/eitrtechnologies/idem-azurerm/pull/53) - Added virtual machine "cleanup"
  functionality similar to that present in salt-cloud.
- [#47](https://github.com/eitrtechnologies/idem-azurerm/pull/47) - Added virtual machine creation
  functionality to create feature parity with salt-cloud, plus more.
- [#35](https://github.com/eitrtechnologies/idem-azurerm/pull/35) - Added virtual machine extension execution
  and state modules.
- [#33](https://github.com/eitrtechnologies/idem-azurerm/pull/33) - Added PostgreSQL replica and location-based
  performance tier support.
- [#26](https://github.com/eitrtechnologies/idem-azurerm/pull/26) - Added PostgreSQL log files, virtual network
  rules, and server security alert policies operations.
- [#25](https://github.com/eitrtechnologies/idem-azurerm/pull/25) - Added initial PostgreSQL support for basic
  deployments.
- [#20](https://github.com/eitrtechnologies/idem-azurerm/pull/20) - Added execution and state modules for
  deploying keys to Key Vaults.
- [#19](https://github.com/eitrtechnologies/idem-azurerm/pull/19) - Added Management Group execution and state
  modules.
- [#13](https://github.com/eitrtechnologies/idem-azurerm/pull/13) - Added Log Analytics Workspace management
  execution and state modules.
- [#10](https://github.com/eitrtechnologies/idem-azurerm/pull/10) - Added encrypted disk functionality to
  virtual machines.
- [#9](https://github.com/eitrtechnologies/idem-azurerm/pull/9) - Added Redis execution and state modules for
  management of the hosted service in Azure.
- [#7](https://github.com/eitrtechnologies/idem-azurerm/pull/7) - Added execution and state modules for Key
  Vault management.
- [#6](https://github.com/eitrtechnologies/idem-azurerm/pull/6) - Added diagnostic setting and management lock
  state modules.
- [#5](https://github.com/eitrtechnologies/idem-azurerm/pull/5) - Added storage execution and state modules for
  storage account and storage container management.
- Added support for Azure Identity Provider credentials.

### Changed

- [#57](https://github.com/eitrtechnologies/idem-azurerm/pull/57) - Changed azurearm references and renamed to
  idem-azurerm to match pip
- [#29](https://github.com/eitrtechnologies/idem-azurerm/pull/29) - Added function aliases for list functions,
  changing the way they are referenced.

### Fixed

- [#42](https://github.com/eitrtechnologies/idem-azurerm/pull/42) - Fixed reference to salt modules for file
  handling in Policy modules.
- [#27](https://github.com/eitrtechnologies/idem-azurerm/pull/27) - Allowed keyword arguments for absent states
  in order to prevent throwing errors and more closely mirror the present states.

### Deprecated

### Removed

## [1.0.0] - 2019-11-14

### Added

- Initial release of execution and state modules from Salt along with some additional functionality ported from
  salt-cloud for virtual machines.

[2.0.0]: https://github.com/eitrtechnologies/idem-azurerm/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/eitrtechnologies/idem-azurerm/releases/tag/v1.0.0
