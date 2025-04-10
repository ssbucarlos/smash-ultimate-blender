from . import attribute_renamer
from . import create_meshes
from . import eye_material_custom_vector_31_modal
from . import misc_panel
from . import set_linear_vertex_color
from . import create_ik_arms
from . import create_ik_armsandlegs
from . import create_ik_legs
from . import bone_removal
from . import apply_ik_animation
from . import hip_animation_transfer
from . import idle_pose_library
from . import ik_influence_toggle
from . import limit_weights
from . import fk_to_ik
from . import rename_utils

# Import reset_animation module and ensure it's properly registered
from . import reset_animation

# Explicit registration function for the package
def register():
    # Register reset_animation first to ensure it's available for the panel
    reset_animation.register()
    
def unregister():
    # Unregister reset_animation
    reset_animation.unregister()