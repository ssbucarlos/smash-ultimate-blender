# Check if a binary is available for the current platform.
# These builds are extracted from the wheels published here:
# https://github.com/BenHall-7/pyprc/releases
# TODO: There may be an easier way in future Blender versions.
from sys import platform
if platform.startswith('win'):
    from .win.pyprc import *
elif platform.startswith('lin'):
    from .linux.pyprc import *
elif platform.startswith('dar'):
    '''
    pyprc doesnt have arm64 macos support
    
    try:
        from .macos.arm64.pyprc import *
    except:
        from .macos.x86.pyprc import *
    '''
    from .macos.x86.pyprc import * 