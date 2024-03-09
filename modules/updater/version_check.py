import re
import requests

from ...__init__ import bl_info

LATEST_VERSION: tuple[int, int, int] = None

def check_for_newer_version():
    try:
        response = requests.get("https://api.github.com/repos/ssbucarlos/smash-ultimate-blender/releases/latest", timeout=.5)
    except Exception as e:
        print(f"Smash_ultimate_blender: Couldn't check for newer version, please check your internet connection. exception info=`{e}`")
        return
    
    try:
        latest_version_tag = response.json().get("tag_name")
    except Exception as e:
        print(f"Smash_ultimate_blender: Couldn't check for newer version, failed to decode JSON response from github. exception info=`{e}`")
        return
    
    if latest_version_tag:
        pattern = r"^v(\d*)\.(\d*)\.(\d*)"
        match = re.match(pattern, latest_version_tag)
        if match is None:
            print("Smash_ultimate_blender: Unable to parse version tag from github request.")
            return
        major, minor, patch = match.groups()
        global LATEST_VERSION
        LATEST_VERSION = (int(major), int(minor), int(patch))
        print(f"Smash_ultimate_blender: The current version is {bl_info['version']}, the latest version is {LATEST_VERSION}")
    else:
        print("Smash_ultimate_blender: Unable to check for newer version, unable to receive version_tag from github.")