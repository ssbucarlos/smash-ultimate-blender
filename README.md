# smash-ultimate-blender
Blender Plugin that contains utilities for Smash Ultimate Models and (eventually) Animations.

# Installation
Click the 'Code' button, download the code as a .ZIP, install that .ZIP in Blender 2.93+. Do not unzip!

The plugin supports 64-bit versions of Windows, Linux, and MacOS. Apple machines with M1 processors are also supported.
If your computer can run Blender 2.93 or later but fails to install the plugin, please make an issue in [issues](https://github.com/ssbucarlos/smash-ultimate-blender/issues).
The exo skel features still require a windows machine, but it's possible to build ssbh_lib_json from source for Linux or MacOS with Rust installed.

# Un-Installation / Updating (Please Read!)
TO REMOVE: First "Disable" the plugin, then restart blender, then you can hit "Remove" to uninstall. Then u can install the newest version.

# Usage
1. Before you import a model, make sure all the textures have been converted to .PNGs. The recommended tool for this is 'Switch Toolbox' (https://github.com/KillzXGaming/Switch-Toolbox)
2. After installing the plugin in blender, in the 3D Viewport pull up the Sidebar (Hotkey is 'N'), and look for the new 'Ultimate' tab in the Sidebar 
* ![image](https://user-images.githubusercontent.com/77519735/131579719-3bf859ac-40ad-4661-8b4c-0d0d0e34da8a.png)

# In case of problems?
1. Export Issues? Please go read the wiki page and see if your issue gets fixed, if not...
2. Please read the wiki to see if that issue is mentioned in the 'List of Known Issues' wiki page, if not...
3. Please go add a new issue in the Issues page so i can track the problem, or message me about it.

# Current Features
1.  Creates the .NUSKTB and .NUHLPB needed for real-time animation retargeting on custom models.
2.  .NUMDLB, .NUMSHB, .NUSKTB, .NUMATB, .NUMSHEXB Import And Export

# Planned Features
1. Complete Import - Export of Models, Materials, Animations
2. Helper Bone visualization
3. Swing Bone visualization

# Dependencies
1. ssbh_lib_json.exe is currently needed for the EXO SKEL only, to convert the outputted .JSON https://github.com/ultimate-research/ssbh_lib Eventually, ssbh_lib will be called directly without needing the user to convert exported JSON
2. Switch Toolbox (to convert .NUTEXBS to .PNGS) https://github.com/KillzXGaming/Switch-Toolbox

# Special Thanks
* SMG for creating SSBH_DATA_PY, which without it none of this would be possible https://github.com/ScanMountGoat/ssbh_data_py
(and also for providing alot of the reference code for how to use the library, most of which was shamelessly stolen and implemented here)
(and also for making CrossMod which was a great reference for how smash ultimate shaders work, from the CrossMod render code certain details such as which step of the shading process do vertex colors get factored in was used)
* The Rokoko plugin https://github.com/Rokoko/rokoko-studio-live-blender for being the reference used for the UI code used in this project.
