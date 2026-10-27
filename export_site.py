"""Stage only dashboard assets for static hosting; never publish local admin files."""
import shutil
import html
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    output = ROOT / "public"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    shutil.copy2(ROOT / "index.html", output / "index.html")
    # Only the public key is embedded. The secret key stays in Vercel's server
    # environment and is used exclusively by middleware.js.
    public_key = os.environ.get("CLERK_PUBLISHABLE_KEY")
    if public_key:
        frontend = "https://clerk.life.aisimple.co"
        auth_scripts = (
            f'<script defer crossorigin="anonymous" src="{frontend}/npm/@clerk/ui@1/dist/ui.browser.js"></script>'
            f'<script defer crossorigin="anonymous" data-clerk-publishable-key="{html.escape(public_key, quote=True)}" '
            f'src="{frontend}/npm/@clerk/clerk-js@6/dist/clerk.browser.js"></script>'
            '<script defer src="/auth-client.js"></script>'
        )
        page = (output / "index.html").read_text()
        (output / "index.html").write_text(page.replace("</body>", auth_scripts + "\n</body>"))
        shutil.copy2(ROOT / "auth-client.js", output / "auth-client.js")
    for name in ("thumbs", "clips"):
        if (ROOT / name).is_dir():
            shutil.copytree(ROOT / name, output / name)
    print("Exported dashboard, thumbnails, and clips to public/")


if __name__ == "__main__":
    main()
