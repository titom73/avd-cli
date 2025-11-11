# Release Notes

## Unreleased

### New Features

- ✨ **EOS Configuration Deployment**: Deploy configurations to Arista EOS devices via eAPI
  - Atomic deployment with config session validation
  - Dry-run mode for safe validation
  - Configuration diff display with statistics
  - Group-based deployment filtering
  - Concurrent deployment with configurable limits
  - SSL verification support for production environments
  - Comprehensive error handling and reporting
  - **Enhanced UI**: Streamlined progress display with diff statistics
    - Removed per-device progress bars for cleaner output
    - Added Diff (+/-) column showing added/removed lines with color coding
    - Color-coded diff statistics (green for additions, red for deletions)

## v0.1.0 (2025-01-XX)

### Initial Release

- ✨ Configuration generation with pyavd
- ✨ Documentation generation
- ✨ Multi-fabric support
- ✨ Environment variable support
- ✨ Rich terminal output

See [CHANGELOG.md](https://github.com/titom73/avd-cli/blob/main/CHANGELOG.md) for complete history.
