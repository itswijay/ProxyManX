"""
ProxyManX Windows - Package initialization

Metadata only. Importing the submodules here would pull in colorama at
package-import time, which breaks reading __version__ before dependencies
are installed.
"""

__version__ = "2.1.0"
__author__ = "Pubudu Wijesundara"
__description__ = "Comprehensive Windows proxy configuration tool"
