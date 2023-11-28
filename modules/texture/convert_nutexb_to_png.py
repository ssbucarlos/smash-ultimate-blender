from sys import platform
from platform import processor
from pathlib import Path
from subprocess import run

def get_ultimate_tex_path() -> Path:
    base_path = Path(__file__).parent.parent.parent / "ultimate_tex"
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

def convert_nutexb_to_png(filepath: Path):
    ultimate_tex_path = get_ultimate_tex_path()
    out_path = filepath.parent / (filepath.stem + ".png")
    run([ultimate_tex_path, str(filepath),  str(out_path)])

def batch_convert_nutexb_to_png(dir: Path):
    nutexb_paths: set[Path] = {path for path in dir.glob("*.nutexb")}
    png_paths: set[Path] = {path for path in dir.glob("*.png")}
    missing_png_stems: set[str] = {nutexb_path.stem for nutexb_path in nutexb_paths} - {png_path.stem for png_path in png_paths}
    
    for nutexb_path in nutexb_paths:
        if nutexb_path.stem in missing_png_stems:
            convert_nutexb_to_png(nutexb_path)

def main():
    test_path = Path(r"C:\Users\Carlos\Documents\Switch Modding\Mod Creation\Programs For Modding\ArcCross\root\fighter\captain\model\body\c00")
    batch_convert_nutexb_to_png(test_path)

if __name__ == '__main__':
    main()

