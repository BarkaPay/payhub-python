# Changelog

All notable changes to this project are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Initial Python SDK: `PayHub` client with `payments`, `transfers`, `balance`,
  `operators` resources plus `ping()` / `me()`.
- Typed data objects (`Payment`, `Transfer`, `Balance`, `Pagination`) and status
  enums (`PaymentStatus`, `TransferStatus`).
- Webhook signature verification (`payhub.webhook.verify` / `parse`).
- Typed exception hierarchy mapped from the API error envelope.
- Zero-dependency `urllib` transport with automatic retries on 429/503/network,
  and an injectable `Transport` for tests.
