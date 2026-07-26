import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def stage_data(source, destination):
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("*.bak", "__pycache__"),
    )


def build_rom(output_path):
    ndstool = ROOT / "ndstool.exe"
    if not ndstool.exists():
        raise FileNotFoundError("ndstool.exe is required in the project root")

    output_path = output_path.resolve()

    with tempfile.TemporaryDirectory(prefix="reids-build-") as temp_dir:
        staged_data = Path(temp_dir) / "data"
        stage_data(ROOT / "data", staged_data)

        command = [
            str(ndstool),
            "-c",
            str(output_path),
            "-9",
            str(ROOT / "arm9.bin"),
            "-7",
            str(ROOT / "arm7.bin"),
            "-y9",
            str(ROOT / "y9.bin"),
            "-y7",
            str(ROOT / "y7.bin"),
            "-d",
            str(staged_data),
            "-y",
            str(ROOT / "overlay"),
            "-t",
            str(ROOT / "banner.bin"),
            "-h",
            str(ROOT / "header.bin"),
        ]
        subprocess.run(command, check=True, cwd=ROOT)

    print(f"Built ROM without backup files: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Build the translated Nintendo DS ROM.")
    parser.add_argument(
        "output",
        nargs="?",
        default="rei.nds",
        type=Path,
        help="Output ROM path (default: rei.nds)",
    )
    args = parser.parse_args()
    build_rom(args.output)


if __name__ == "__main__":
    main()
