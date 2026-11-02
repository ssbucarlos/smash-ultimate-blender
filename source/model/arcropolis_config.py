"""Create fighter mod folders and merge ARCropolis texture registrations.

Config format: https://github.com/Raytwo/ARCropolis/blob/master/src/modfs/handlers/config.rs
"""

import json
import os
from pathlib import Path
import re
import tempfile


def target_from_vanilla(path: str) -> tuple[str, str] | None:
    """Read the fighter and costume from an extracted body skeleton's path.

    Use both separator styles regardless of the host OS. A bare model.nusktb
    or a renamed texture cannot identify a costume, so leave those unresolved.
    """
    match = re.search(r'(?:^|/)([a-z0-9_]+)/model/body/(c0[0-7])/[^/]+\.nusktb$',
                      path.replace('\\', '/'), flags=re.IGNORECASE)
    return (match[1].lower(), match[2].lower()) if match else None


def model_folder(mod_root: Path, fighter: str, costume: str) -> Path:
    fighter = fighter.strip().lower()
    if not re.fullmatch(r'[a-z0-9_]+', fighter):
        raise ValueError('Enter the internal fighter name, for example ken or captain.')
    if not re.fullmatch(r'c0[0-7]', costume):
        raise ValueError('Choose an existing costume slot from c00 through c07.')
    return Path(mod_root) / 'fighter' / fighter / 'model' / 'body' / costume


def read_config(mod_root: Path) -> dict:
    path = Path(mod_root) / 'config.json'
    config = json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError('Existing config.json must contain a JSON object.')
    # ARCropolis also accepts these aliases. Keep an existing spelling instead
    # of introducing duplicate serde fields that would make the config invalid.
    keys = [key for key in ('new-dir-files', 'new_dir_files') if key in config]
    if len(keys) > 1:
        raise ValueError('config.json contains both new-dir-files and new_dir_files.')
    additions = config.get(keys[0], {}) if keys else {}
    if not isinstance(additions, dict) or any(
        not isinstance(files, list) or any(not isinstance(name, str) for name in files)
        for files in additions.values()
    ):
        raise ValueError('config.json new-dir-files must map folder names to lists of file paths.')
    return config


def write_config(mod_root: Path, fighter: str, costume: str, textures) -> Path:
    """Register only successfully exported textures, preserving other settings."""
    mod_root = Path(mod_root).resolve()
    folder = model_folder(mod_root, fighter, costume).resolve()
    config = read_config(mod_root)
    names = set()
    for texture in textures:
        texture = Path(texture).resolve()
        if texture.parent != folder or texture.suffix.lower() != '.nutexb':
            raise ValueError(f'Exported texture is outside the selected model folder: {texture}')
        if not texture.is_file():
            raise ValueError(f'Exported texture does not exist: {texture}')
        names.add(texture.relative_to(mod_root).as_posix())
    if names:
        field = 'new_dir_files' if 'new_dir_files' in config else 'new-dir-files'
        additions = config.setdefault(field, {})
        key = f'fighter/{fighter.strip().lower()}/{costume}'
        additions[key] = sorted(set(additions.get(key, [])) | names)

    mod_root.mkdir(parents=True, exist_ok=True)
    path = mod_root / 'config.json'
    # A cancelled or failed write must not truncate the user's working config.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=mod_root, prefix='.config-', suffix='.tmp',
                                         delete=False) as output:
            temporary = Path(output.name)
            json.dump(config, output, indent=2, ensure_ascii=False)
            output.write('\n')
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return path
