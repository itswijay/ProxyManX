# ProxyManX Windows - Changelog

## v2.1.0 - Packaging and Correctness

### Breaking Changes

- **Passwords are no longer saved to profiles.** A profile stores the username
  only; `proxymanx load` prompts for the password when the profile uses
  authentication. Existing profiles that contain a password still load, and the
  password is dropped the next time that profile is saved.
- **`python proxymanx.py` is gone.** The top-level script has been replaced by a
  real package — use `proxymanx`, or `python -m proxymanx` when running from a
  checkout. `proxymanx.bat` has been updated accordingly.
- **Existing installations must be re-installed.** The launcher on your PATH
  points at the removed script. Run `pip install .` or `python install.py` again.

### Added

- `pip install .` now produces a working `proxymanx` command. The package was
  previously unimportable when installed, because the modules used flat imports
  that only resolved through a `sys.path` shim.
- `proxymanx save <name>` is implemented. It reads the proxy settings currently
  live on the system — from the environment, falling back to the Windows system
  proxy — and stores them as a profile. It was previously a stub that printed
  "use `set` instead".
- A pytest suite covering profile storage, URL parsing, config validation and
  the environment target. Run with `pip install -e ".[dev]"` then `pytest`.
- GitHub Actions workflow that runs the tests on Linux and Windows, and runs the
  PowerShell installer, all five targets and the uninstaller on Windows.
- `-NoPause` option for `install.ps1` and `uninstall.ps1`, for unattended use.

### Fixed

- `proxymanx delete <name>` silently failed for `.json` profiles. They were
  listed by `list` but only `.ini` files were ever removed.
- `proxymanx set` did not record the new profile as active, so `list` reported
  "no active profile" immediately after creating one. Declining to save now
  clears the previously active profile instead of leaving a stale pointer.
- `PowerShellProxyTarget.is_available()` returned `True` on every platform, so
  on Linux and macOS the target went live and wrote a profile into
  `~/Documents/WindowsPowerShell/`.
- `validate_proxy_config` raised `TypeError` instead of validating when given a
  port as a string.
- The PowerShell uninstaller invoked `unset` without `all` and would hang on the
  interactive prompt — the same bug fixed for the Python uninstaller in 2.0.0.
- Proxy usernames and passwords with characters such as `#`, `/` or `@` broke the
  proxy URL. They are now encoded. Values containing `%` can be saved too.
- New terminals now see the proxy without signing out. Windows was told about
  the change before the variables were written.
- The bypass list is written in the form each tool expects: `10.*;*.local` for
  the Windows system proxy, `10.0.0.0/8,.local` for `NO_PROXY`.
- npm certificate checking (`strict-ssl`) is no longer turned off. `set` warns if
  an older version left it off, and `unset` turns it back on.
- `configs` showed npm as active even with no proxy set.
- `unset` could delete the user's own lines after the ProxyManX block in the
  PowerShell profile. A profile that cannot be read is now left untouched.
- Programs using the Windows system proxy are told to reload it after a change.
- Running the tests on Windows no longer overwrites the user's proxy settings.
- `install.ps1` had a stray closing brace after `Install-Dependencies`, a syntax
  error that stops PowerShell from running the script.
- Saving, deleting or failing to load a profile crashed on Windows when the output
  was piped, because the messages contained emoji. `set` then failed to record
  the active profile.
- The launcher created by `install.ps1` ran the command a second time after any
  error. It now uses `py` only when `python` is unavailable, and no longer
  changes the caller's current directory.
- `deploy.py` still packaged `proxyman.py`, `proxyman.bat` and the deleted
  `install-simple.ps1`, so its output was missing the application entirely.
- The declared version (`1.0.0`) disagreed with the CHANGELOG. `__version__` in
  `proxymanx/__init__.py` is now the single source of truth, read by `setup.py`.

### Changed

- `src/` is now the `proxymanx` package: `src/proxymanx.py` became
  `proxymanx/cli.py`, all intra-package imports are relative, and the
  `from utils import *` wildcards were replaced with explicit imports.
- Dropped the unused `click` dependency.
- README lists the 5 targets that actually exist (it previously advertised 7).

## v2.0.0 - ProxyManX Release (Professional Version)

### Major Changes

- 🎯 **Rebranded to ProxyManX** - Professional version with enhanced branding
- 📁 **Updated file structure** - All executables renamed to `proxymanx.*`
- 🔧 **Updated commands** - All CLI commands now use `proxymanx` instead of `proxyman`
- 📂 **New config directory** - Configuration files now stored in `%USERPROFILE%\.proxymanx\`
- 🔗 **Updated repository** - New repository structure for ProxyManX branding

### Breaking Changes

- Command name changed from `proxyman` to `proxymanx`
- Batch file renamed from `proxyman.bat` to `proxymanx.bat`
- Main executable renamed from `proxyman.py` to `proxymanx.py`
- Configuration directory moved from `.proxyman` to `.proxymanx`

### Migration Guide

- Existing installations should be uninstalled before upgrading
- Configuration files will need to be recreated or migrated manually
- Update any scripts or shortcuts to use the new `proxymanx` command

## v1.0.0 - Initial Release

### Features

- ✅ **System-wide proxy configuration** for Windows
- ✅ **Interactive CLI** with colorized output
- ✅ **Profile management** - save, load, and delete configurations
- ✅ **Multiple target support**:
  - Windows system proxy settings (Registry)
  - Environment variables
  - Git configuration
  - NPM/Yarn configuration
  - PowerShell profile
- ✅ **Authentication support** for proxy servers
- ✅ **Batch operations** on multiple targets
- ✅ **Cross-platform compatibility** (Windows 10/11)

### Supported Targets

1. **System Proxy** - Windows system proxy settings via Registry
2. **Environment Variables** - User environment variables (HTTP_PROXY, HTTPS_PROXY)
3. **Git** - Global git proxy configuration
4. **NPM** - NPM/Yarn proxy settings
5. **PowerShell** - PowerShell profile proxy settings

### Technical Details

- Built with Python 3.7+
- Uses Windows Registry for system proxy settings
- Colorized terminal output with colorama
- Configuration files stored in `%USERPROFILE%\.proxymanx\`
- Automatic detection of available tools (git, npm, etc.)

### Installation

- Simple installation script (`install.py`)
- Automatic dependency installation
- Optional PATH configuration
- Batch file for easy execution

### Known Limitations

- Some operations require administrator privileges
- Registry changes may require system restart for some applications
- PowerShell profile changes require restarting PowerShell

### Future Enhancements

- Support for additional targets (Docker, Chrome, Firefox)
- GUI interface
- Automatic proxy detection
- Import/export configurations
- Proxy testing and validation

---

_Based on the original ProxyMan project for Linux by Himanshu Shekhar_
