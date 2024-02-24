from sys import platform
if platform.startswith('win'):
    from .win.ssbh_mesh_optimizer import *