# Changelog

All notable changes to the ToyyibPay Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Fixed
- Nothing yet

## [0.1.1] - 2025-06-22

### Added
- Initial release of ToyyibPay Python SDK
- Synchronous client for API operations
- Asynchronous client support with `AsyncClient`
- Full type hints and Pydantic models
- Comprehensive error handling with custom exceptions
- PostgreSQL database integration for payment tracking
- Webhook handling with event-based callbacks
- Flask integration support
- FastAPI integration support
- Extensive test suite with >95% coverage
- Complete documentation
- CI/CD pipeline with GitHub Actions

### Features
- **Payment Operations**
  - Create bills/payments
  - Check payment status
  - Get bill transactions
  - Create payment categories

- **Database Support**
  - PostgreSQL integration (MySQL and MongoDB coming soon)
  - Payment record tracking
  - Soft delete support
  - Transaction history

- **Webhook Support**
  - Event handlers for payment success/failure
  - Signature verification (when available)
  - Framework-agnostic webhook processing

- **Framework Integration**
  - Flask: Decorators and utilities
  - FastAPI: Dependency injection and models

- **Developer Experience**
  - Clean, intuitive API similar to Stripe
  - Comprehensive type hints
  - Detailed error messages
  - Extensive documentation
  - Example applications

### Known Issues
- Webhook signature verification pending ToyyibPay documentation
- Rate limiting not yet implemented (coming in 0.2.0)
- Batch operations not yet supported (coming in 0.2.0)

### Breaking Changes
- None (initial release)

### Security
- Secure by default configuration
- API key validation
- Optional SSL verification
- No credentials in logs

---

[Unreleased]: https://github.com/waizwafiq/toyyibpay-python/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/waizwafiq/toyyibpay-python/releases/tag/v0.1.1