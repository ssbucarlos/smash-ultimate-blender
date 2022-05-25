# smash-ultimate-blender
Blender Plugin that contains utilities for Smash Ultimate Models and (eventually) Animations.

## Installation
1. Click the green Code button and select Download ZIP. Don't unzip the file.
2. Install the .ZIP in Blender under Edit > Preferences > Addons > Install. 
3. Make sure the addon is enabled by searching for "Smash Ultimate".

The plugin supports 64-bit versions of Blender 2.93 or 3.0 for Windows, Linux, and MacOS. Apple machines with M1 processors are also supported.
If your computer can run a supported version of Blender but fails to install the plugin, please make an issue in [issues](https://github.com/ssbucarlos/smash-ultimate-blender/issues). The exo skel features still require a windows machine, but it's possible to build [ssbh_lib_json](https://github.com/ultimate-research/ssbh_lib) from source for Linux or MacOS with Rust installed.

Blender 3.1 support is planned for a future update but not supported at this time. You can download Blender 3.0 from https://download.blender.org/release/Blender3.0/

## Un-Installation / Updating (Please Read!)
TO REMOVE: First "Disable" the plugin, then restart blender, then you can hit "Remove" to uninstall. Then u can install the newest version.

## Usage
1. Before you import a model, make sure all the textures have been converted to .PNGs. The recommended tool for this is 'Switch Toolbox' (https://github.com/KillzXGaming/Switch-Toolbox)
2. After installing the plugin in blender, in the 3D Viewport pull up the Sidebar (Hotkey is 'N'), and look for the new 'Ultimate' tab in the Sidebar 
* ![image](https://user-images.githubusercontent.com/77519735/131579719-3bf859ac-40ad-4661-8b4c-0d0d0e34da8a.png)

## In case of problems?
1. Export Issues? Please go read the [export issues](https://github.com/ssbucarlos/smash-ultimate-blender/wiki/Read-this-if-you-have-export-issues.-Or-want-to-avoid-Export-Issues) wiki page and see if your issue gets fixed, if not...
2. Please read the wiki to see if that issue is mentioned in the [List of Known Issues](https://github.com/ssbucarlos/smash-ultimate-blender/wiki/Known-Blender-Issues) wiki page, if not...
3. Please go add a new issue in the Issues page so i can track the problem, or message me about it.

## Current Features
1.  Creates the .NUSKTB and .NUHLPB needed for real-time animation retargeting on custom models.
2.  .NUMDLB, .NUMSHB, .NUSKTB, .NUMATB, .NUMSHEXB Import And Export

## Planned Features
1. Animation export
2. Swing bone visualization

## Useful Tools
* Switch Toolbox (to convert .NUTEXBS to .PNGS) https://github.com/KillzXGaming/Switch-Toolbox

## Special Thanks
* SMG for creating SSBH_DATA_PY, which without it none of this would be possible https://github.com/ScanMountGoat/ssbh_data_py
(and also for providing alot of the reference code for how to use the library, most of which was shamelessly stolen and implemented here)
(and also for making CrossMod which was a great reference for how smash ultimate shaders work, from the CrossMod render code certain details such as which step of the shading process do vertex colors get factored in was used)
* The Rokoko plugin https://github.com/Rokoko/rokoko-studio-live-blender for being the reference used for the UI code used in this project.
