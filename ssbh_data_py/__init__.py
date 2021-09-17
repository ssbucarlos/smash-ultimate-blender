# Check if a binary is available for the current platform.
# These builds are extracted from the wheels published here:
# https://github.com/ScanMountGoat/ssbh_data_py/releases
from sys import platform
if platform.startswith('win'):
    from .win.ssbh_data_py import *
elif platform.startswith('lin'):
    from .linux.ssbh_data_py import *
elif platform.startswith('dar'):
    from .macos.ssbh_data_py import *