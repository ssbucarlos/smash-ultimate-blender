import re
import requests

COMPATIBLE_UPDATE_AVAILABLE: bool = None
LATEST_COMPATIBLE_VERSION: tuple[int,int,int] = None

def check_for_newer_version():
    """
    The latest version should only check for a newer version compatible with the current blender version.
    By convention, the major version number will only be incremented with a breaking blender version change,
    meanwhile the minor version or patch version will be incremented on a new feature compatible with the current blender install.
    Also, dont want to notify users of a beta release.
    Many users won't be able to upgrade to a newer blender version right away, so don't notify them of an update they can't install yet.
    """
    from ...__init__ import bl_info

    try:
        response = requests.get("https://api.github.com/repos/ssbucarlos/smash-ultimate-blender/git/refs/tags", timeout=.5)
    except Exception as e:
        print(f"Smash_ultimate_blender: Couldn't check for newer version, please check your internet connection. exception info=`{e}`")
        return
    
    #example of "refs" {'refs/tags/v1.3.0', 'refs/tags/v1.3.1',...}
    refs = {s.get("ref") for s in response.json()}
    regex_pattern = r"^refs/tags/v(\d*)\.(\d*)\.(\d*)$"
    current_major, current_minor, current_patch = bl_info["version"][0], bl_info["version"][1], bl_info["version"][2]
    current_minor_patch_version = (current_minor, current_patch)

    for ref in refs:
        if match:= re.match(regex_pattern, ref):
            if groups:= match.groups():
                found_major, found_minor, found_patch = int(groups[0]), int(groups[1]), int(groups[2])
                found_version = (found_major, found_minor, found_patch)
                found_minor_patch_version = (found_minor, found_patch)
                if found_major == current_major:
                    if current_minor_patch_version < found_minor_patch_version:
                        global COMPATIBLE_UPDATE_AVAILABLE
                        global LATEST_COMPATIBLE_VERSION
                        COMPATIBLE_UPDATE_AVAILABLE = True
                        if LATEST_COMPATIBLE_VERSION is None:
                            LATEST_COMPATIBLE_VERSION = found_version
                        elif LATEST_COMPATIBLE_VERSION < found_version:
                            LATEST_COMPATIBLE_VERSION = found_version
    