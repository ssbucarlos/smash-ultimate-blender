import re
import requests

from ...__init__ import bl_info

LATEST_VERSION: tuple[int, int, int] = None

def check_for_newer_version():
    response = requests.get("https://api.github.com/repos/ssbucarlos/smash-ultimate-blender/releases/latest")
    latest_version_tag = response.json().get("tag_name")

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