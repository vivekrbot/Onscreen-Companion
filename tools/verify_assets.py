from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
EXPECTED = {"idle": 60, "hover": 60, "fire": 60, "click": 60}
SIZE = (360, 240)

total = 0
for state, count in EXPECTED.items():
    files = sorted((ASSETS / state).glob(f"{state}_*.png"))
    if len(files) != count:
        raise SystemExit(f"Expected {count} {state} frames, found {len(files)}")
    for path in files:
        with Image.open(path) as image:
            if image.mode != "RGBA":
                raise SystemExit(f"{path.name} must be RGBA, found {image.mode}")
            if image.size != SIZE:
                raise SystemExit(f"{path.name} must be {SIZE}, found {image.size}")
            alpha = image.getchannel("A")
            if alpha.getextrema() != (0, 255):
                raise SystemExit(f"{path.name} does not contain clean transparency")
            corners = [alpha.getpixel((0, 0)), alpha.getpixel((SIZE[0]-1, 0)),
                       alpha.getpixel((0, SIZE[1]-1)), alpha.getpixel((SIZE[0]-1, SIZE[1]-1))]
            if any(corners):
                raise SystemExit(f"{path.name} has non-transparent canvas corners")
    total += count

print(f"Verified {total} native-resolution transparent animation frames.")
