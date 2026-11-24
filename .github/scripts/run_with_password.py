"""Run proxymanx with the password taken from TEST_PROXY_PASSWORD, used by CI only.

On Windows the password prompt reads the keyboard directly, so CI cannot pipe
an answer to it.
"""

import getpass
import os

from proxymanx.cli import main

getpass.getpass = lambda prompt="": os.environ["TEST_PROXY_PASSWORD"]
main()
