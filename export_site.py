"""Stage only dashboard assets for static hosting; never publish local admin files."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    output = ROOT / "public"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    shutil.copy2(ROOT / "index.html", output / "index.html")
    for name in ("thumbs", "clips"):
        if (ROOT / name).is_dir():
            shutil.copytree(ROOT / name, output / name)
    print("Exported dashboard, thumbnails, and clips to public/")


if __name__ == "__main__":
    main()
