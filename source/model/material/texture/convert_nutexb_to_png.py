from sys import platform
from platform import processor
from pathlib import Path
from subprocess import run

def get_ultimate_tex_path() -> Path:
    base_path = Path(__file__).parent.parent.parent.parent.parent / "dependencies" / "ultimate_tex"
    if platform.startswith('win'):
        return base_path / "win" / "ultimate_tex_cli.exe"
    elif platform.startswith('lin'):
        return base_path / "linux" / "ultimate_tex_cli"
    elif platform.startswith('dar'):
        if processor() == "arm":
            return base_path / "macos"/ "arm64" / "ultimate_tex_cli"
        elif processor() == "i386":
            return base_path / "macos"/ "x86" / "ultimate_tex_cli"
        else:
            raise RuntimeError(f"On macos but with unknown processor{processor()}")
    else:
        raise RuntimeError(f"Unknown platform `{platform}`")

def convert_nutexb_to_png(nutexb_filepath: Path, output_filepath: Path):
    ultimate_tex_path = get_ultimate_tex_path()
    run([ultimate_tex_path, str(nutexb_filepath),  str(output_filepath)], capture_output=True, check=True)

def batch_convert_nutexb_to_png(dir: Path):
    nutexb_paths: set[Path] = {path for path in dir.glob("*.nutexb")}

    for nutexb_path in nutexb_paths:
        out_path = nutexb_path.parent / (nutexb_path.stem + ".png")
        convert_nutexb_to_png(nutexb_path, out_path)

def main():
    test_path = Path(r"C:\Users\Carlos\Documents\Switch Modding\Mod Creation\Programs For Modding\ArcCross\root\fighter\captain\model\body\c00")
    batch_convert_nutexb_to_png(test_path)

if __name__ == '__main__':
    main()

