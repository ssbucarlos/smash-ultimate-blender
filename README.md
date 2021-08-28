# smash-ultimate-blender
Blender Plugin that (will eventually contatin) utilities for Smash Ultimate Models and Animations.

# Installation
Click the 'Code' button, download the code as a .ZIP, install that .ZIP in Blender 2.93+. Do not unzip!

# Un-Installation (Please Read!)
TO REMOVE: First "Disable" the plugin, then restart blender, then you can hit "Remove" to uninstall.

# Usage
After installing the plugin in blender, in the 3D Viewport pull up the Sidebar (Hotkey is 'N'), and look for the new 'Ultimate' tab in the Sidebar.

# Current Features
1.  Creates the .NUSKTB and .NUHLPB needed for real-time animation retargeting on custom models.
2.  .NUMDLB, .NUMSHB, .NUSKTB Import And Export
3.  .NUMATB import

# Planned Features
1. Import - Export of Models, Materials, Animations
2. Helper Bone visualization
3. Swing Bone visualization

# Dependencies
ssbh_lib_json.exe is currently needed for the EXO SKEL only, to convert the outputted .JSON https://github.com/ultimate-research/ssbh_lib
Eventually, ssbh_lib will be called directly without needing the user to convert exported JSON

# Please Note!
This is not the model.numdlb importer script! 
# Special Thanks
SMG for creating SSBH_DATA_PY, which without it none of this would be possible https://github.com/ScanMountGoat/ssbh_data_py
(and also for providing alot of the reference code for how to use the library, most of which was shamelessly stolen and implemented here)
