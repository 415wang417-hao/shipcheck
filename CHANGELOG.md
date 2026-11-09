# Changelog

All notable changes to `shipcheck` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2026-11-05

### Added
- Initial release of `shipcheck`
- 8 mandatory check rules for C5 GitHub Repository compliance
- 4 bonus check rules (CONTRIBUTING, CHANGELOG, CI/CD, Issue templates)
- CLI interface: `shipcheck <path>` with `--format` and `--only-failures` flags
- Terminal reporter with emoji status indicators (✅ ❌)
- JSON output mode for CI integration (`--format json`)
- `examples/sample_project/` — a minimal compliant repo for reference
- `tests/` — 18 pytest test cases covering all rules
- `scripts/run_check.py` — standalone script requiring no installation
- Full documentation: README, AI_LOG, ATTRIBUTION, CONTRIBUTING, CHANGELOG
- Issue templates: Bug Report, Feature Request

### Notes
- Requires Python 3.9+, no third-party dependencies
- Works on Windows, macOS, and Linux
- Checks local directories only (no GitHub API calls needed)
