# smash-ultimate-blender 
[![wiki](https://img.shields.io/badge/wiki-guide-success)](https://github.com/ssbucarlos/smash-ultimate-blender/wiki)

Blender Plugin that contains utilities for Smash Ultimate models and animations.

## Current Features
1. Import/Export of Model, Material, Texture, Animation, and Swing files
   - Model Files: `.numdlb`, `.numshb`, `.nusktb`, `.nuhlpb`, `update.prc`, `.numeshexb`, `.adjb`
   - Material & Texture Files: `.numatb`, `.nutexb`
   - Animation Files: `.nuanmb` 
   - Swing Files: `swing.prc`
2. Tools for creating a "Magic Exo Skel" for real-time animation retargeting in-game.
   - UI panel for step-by-step creation
   - Modifier setup for previewing real-time retargeting pre-export
3. Extra QOL Features for Animators
   - Import/Export Camera `.nuanmb`
   - Drivers for previewing `Visibilty` and `Material` data in animation files.
   - UI Panels for easily editing `Visiblity` and `Material` data in animation files.
   - Modal Operator for intuitively editing Characters eyes in animations.

## Installation
Check the [wiki](https://github.com/ssbucarlos/smash-ultimate-blender/wiki) for tutorials and usage instructions. 
1. Select a version
  - For the latest version, click the green `Code` button and select `Download ZIP`.
  - For a specific version, check the "Releases" page.
2. Install the .ZIP in Blender under Edit > Preferences > Addons > Install. 
3. Make sure the addon is enabled by searching for "Smash Ultimate".
4. After installing the plugin in blender, in the 3D Viewport pull up the Sidebar (Hotkey is 'N'), and look for the new 'Ultimate' tab in the Sidebar. **If the addon panel doesn't show up, make sure you are in object mode!**  
![image](https://user-images.githubusercontent.com/77519735/131579719-3bf859ac-40ad-4661-8b4c-0d0d0e34da8a.png)

## System Requirements
The plugin supports 64-bit versions of Blender 4.0 or later for Windows, Linux, and MacOS. Apple machines with M1 processors are also supported.
If your computer can run a supported version of Blender but fails to install the plugin, please make an issue in [issues](https://github.com/ssbucarlos/smash-ultimate-blender/issues).

## Legacy Blender Version Support
* Check the releases page for older versions of the plugin that work for the legacy blender version.
* This started with 3.6 LTS, older versions of blender require digging through the commit history and finding a really old version that worked with that old blender version.

## Uninstalling / Updating (Please Read!)
TO REMOVE: First "Disable" the plugin, then restart blender, then you can hit "Remove" to uninstall. Then you can install the newest version.

## In case of problems?
1. Export Issues? Please go read the [export issues](https://github.com/ssbucarlos/smash-ultimate-blender/wiki/Read-this-if-you-have-export-issues.-Or-want-to-avoid-Export-Issues) wiki page and see if your issue gets fixed, if not...
2. Please read the wiki to see if that issue is mentioned in the [List of Known Issues](https://github.com/ssbucarlos/smash-ultimate-blender/wiki/Known-Blender-Issues) wiki page, if not...
3. Please go add a new issue in the Issues page so the issue can be tracked.

## Useful Tools
* SSBH Editor (view models and animations and edit materials) https://github.com/ScanMountGoat/ssbh_editor
* Ultimate Tex (batch convert .NUTEXB to .PNG on Windows, MacOS, or Linux) https://github.com/ScanMountGoat/ultimate_tex
* Switch Toolbox (to convert .NUTEXB to .PNG on Windows) https://github.com/KillzXGaming/Switch-Toolbox

## Special Thanks
* SMG for creating SSBH_DATA_PY, which without it none of this would be possible https://github.com/ScanMountGoat/ssbh_data_py
(and also for providing alot of the reference code for how to use the library, most of which was shamelessly stolen and implemented here)
(and also for making CrossMod which was a great reference for how smash ultimate shaders work, from the CrossMod render code certain details such as which step of the shading process do vertex colors get factored in was used)
* The Rokoko plugin https://github.com/Rokoko/rokoko-studio-live-blender for being the reference used for the UI code used in this project.
