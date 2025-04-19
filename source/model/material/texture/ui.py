import bpy
from bpy.types import Panel

# Panel removed to avoid confusion - functionality is available through the material properties

# Empty classes tuple (panel removed)
classes = ()

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register() 