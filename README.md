![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# ProxyManX Windows

A comprehensive Windows proxy management tool built with Python.

## Features

- **System-wide proxy configuration** for Windows
- **Profile management** - save, load, and delete proxy configurations
- **Multiple target support**:
  - Windows system proxy settings (Registry)
  - Environment variables
  - Git configuration
  - NPM/Yarn configuration
  - PowerShell profile
- **Interactive CLI** with colorized output
- **Authentication support** for proxy servers
- **Batch operations** on multiple targets

## Requirements

- Python 3.7+
- Windows 10/11
- Administrator privileges (for some operations)

## Installation

### Option 1: pip (Recommended)

```powershell
git clone https://github.com/thewijay/ProxyManX.git
cd ProxyManX

pip install .
```

This installs the `proxymanx` command onto your PATH.

### Option 2: Python Installer

Adds the project directory to your PATH and creates a `proxymanx.bat` launcher.

```powershell
git clone https://github.com/thewijay/ProxyManX.git
cd ProxyManX

python install.py
```

### Option 3: PowerShell Installation

```powershell
# Quick installation (recommended):
.\install.ps1 -Simple

# Advanced installation with options:
.\install.ps1 -SystemWide    # System-wide installation (requires admin)
.\install.ps1 -UserOnly      # User-only installation
.\install.ps1 -SkipPath      # Don't add to PATH

# Standard installation:
.\install.ps1
```

### Option 4: Manual Installation

```powershell
# Install dependencies
pip install -r requirements.txt

# Run without installing
python -m proxymanx help
```

## Uninstallation

To completely remove ProxyManX Windows from your system:

### Option 1: Python Uninstaller

```bash
python uninstall.py
```

### Option 2: PowerShell Uninstaller

```powershell
# Interactive uninstall
.\uninstall.ps1

# Silent uninstall
.\uninstall.ps1 -Force

# Keep configuration files
.\uninstall.ps1 -KeepConfig

# Keep proxy settings
.\uninstall.ps1 -KeepProxy
```

The uninstaller will:

- Remove ProxyManX from PATH
- Delete configuration files and saved profiles
- Remove desktop shortcuts
- Optionally clear all proxy settings set by ProxyManX
- Clean up all installation artifacts

## Usage

### Set Proxy

```bash
proxymanx set
```

### Unset Proxy

```bash
proxymanx unset
```

### List Current Settings

```bash
proxymanx list
```

### Save Configuration

Captures the proxy settings currently live on your system and stores them as a
named profile.

```bash
proxymanx save profile_name
```

### Load Configuration

Applies a saved profile. If the profile uses authentication you are prompted for
the password, since passwords are not stored.

```bash
proxymanx load profile_name
```

### List Configurations

```bash
proxymanx configs
```

### Delete Configuration

```bash
proxymanx delete profile_name
```

### Show Help

```bash
proxymanx help
```

## Supported Targets

1. **System Proxy** - Windows system proxy settings, written via the Registry.
   This is what Internet Explorer, Edge and most GUI applications read.
2. **Environment Variables** - `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`, set for
   the current session and persisted for future ones. Console applications,
   including Command Prompt, pick these up.
3. **Git** - Global git proxy configuration
4. **NPM/Yarn** - Package manager proxy settings
5. **PowerShell** - PowerShell profile proxy settings

Targets are detected at runtime; anything not present on your system (no Git, no
npm, or the Windows-only targets when running elsewhere) is skipped.

## Configuration Files

Profiles are stored in the `%USERPROFILE%\.proxymanx\` directory.

**Passwords are never written to disk.** When a profile uses authentication,
only the username is saved; the password is prompted for each time you run
`proxymanx load`.

## Notes

- Some operations require administrator privileges
- System proxy changes take effect immediately
- Shell proxy settings require restarting the terminal
- Registry changes may require system restart for some applications

## Project Structure

```
ProxyManX/
├── proxymanx/             # Core application package
│   ├── __init__.py        # Package metadata
│   ├── __main__.py        # Entry point for `python -m proxymanx`
│   ├── cli.py             # Command dispatch and interactive flows
│   ├── config.py          # Profile storage
│   ├── targets.py         # Proxy target handlers
│   └── utils.py           # Utility functions
├── tests/                 # pytest suite
├── install.py             # Python installer
├── install.ps1            # Unified PowerShell installer
├── uninstall.py           # Python uninstaller
├── uninstall.ps1          # PowerShell uninstaller
├── proxymanx.bat          # Windows batch launcher
├── setup.py               # Packaging metadata
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Development

```powershell
pip install -e ".[dev]"
pytest
```

## Acknowledgments

This project is inspired by and based on the original [ProxyMan for Linux](https://github.com/himanshub16/ProxyMan) by Himanshu Shekhar. ProxyManX extends the concept to provide comprehensive Windows proxy management with enhanced features and professional tooling.

Original ProxyMan project:
- **Repository**: https://github.com/himanshub16/ProxyMan
- **Author**: Himanshu Shekhar
- **License**: MIT License

## License

MIT License

## Troubleshooting

### Ctrl+C Not Working During Interactive Prompts

**Problem**: When ProxyManX is prompting for input (like proxy host, port, username), pressing Ctrl+C doesn't stop the program immediately.

**Cause**: This was due to input functions not properly handling KeyboardInterrupt signals.

**Solution**: This has been fixed in the latest version. The application now properly handles Ctrl+C during:

- Interactive proxy configuration
- Yes/No prompts
- Password input
- Configuration name input

**If you're still experiencing this issue**:

1. Make sure you're using the latest version
2. Update your installation: `git pull` and `python install.py`
3. As a workaround, you can:
   - Press Ctrl+Z to suspend the process, then `taskkill /f /im python.exe` in another terminal
   - Close the terminal window entirely
   - Use Task Manager to end the Python process

### Common Issues

**Error: "Python not found"**

- Install Python 3.7+ from python.org
- Make sure Python is added to PATH during installation
- Verify with: `python --version`

**Error: "ModuleNotFoundError: No module named 'colorama'"**

- Install dependencies: `pip install -r requirements.txt`
- Make sure you're in the correct project directory

**Error: "proxymanx is not recognized"**

- The tool is not in your system PATH
- Use `.\proxymanx.bat` or `python -m proxymanx` instead
- Or run `pip install .`, which puts `proxymanx` on your PATH
- Or run `python install.py` to add the project directory to PATH

**Error: "Access is denied" or "Permission denied"**

- Run Command Prompt or PowerShell as Administrator
- Some operations (like system proxy, registry changes) require elevated privileges

**Settings not taking effect**

- Some applications may need to be restarted
- System proxy changes are usually immediate
- Environment variables affect new processes only
- Browser settings may require restart

**Git proxy configuration fails**

- Make sure Git is installed and in PATH
- Verify with: `git --version`
- Git proxy configuration will be skipped if Git is not available

### Performance Issues

**Slow startup or operations**

- Check if antivirus is scanning Python processes
- Add ProxyManX directory to antivirus exclusions
- Ensure Python and pip are up to date

**Registry operations taking too long**

- This is normal for first-time registry access
- Subsequent operations should be faster
- Run as Administrator for better performance

### Getting Help

```powershell
# Display help and available commands
proxymanx help
# or
.\proxymanx.bat help
# or
python -m proxymanx help
```

**For additional support**:

- Check the project repository for latest updates
- Report bugs or issues on GitHub
- Review the QUICKSTART.md for detailed usage examples
