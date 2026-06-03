from pathlib import Path
from file_loader import load_file, build_preview
from PIL import Image
from collections import Counter
import math


class Processor:
    def process(self, path: Path) -> dict:
        raise NotImplementedError()


class TextProcessor(Processor):
    def process(self, path: Path) -> dict:
        content = load_file(path)
        preview = build_preview(content)
        return {
            "content": content,
            "preview": preview,
            "dominant_color": None,
        }


class ImageProcessor(Processor):
    def process(self, path: Path) -> dict:
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                img.thumbnail((100, 100))

                counts = Counter()

                for rgb in img.getdata():
                    color_name = _map_rgb_to_name(rgb)
                    counts[color_name] += 1

                dominant_color, _ = counts.most_common(1)[0]

                preview = f"Image - dominant color: {dominant_color}"

                return {
                    "content": "",
                    "preview": preview,
                    "dominant_color": dominant_color,
                }

        except Exception:
            return {
                "content": "",
                "preview": "[image]",
                "dominant_color": None,
            }

def _map_rgb_to_name(rgb):
    named = {
        "red": (255, 0, 0),
        "green": (0, 128, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "pink": (255, 192, 203),
        "brown": (150, 75, 0),
        "gray": (128, 128, 128),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
    }

    def dist(a, b):
        return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))

    best = None
    best_d = None
    for name, c in named.items():
        d = dist(rgb, c)
        if best_d is None or d < best_d:
            best = name
            best_d = d
    return best


def get_processor_for_path(path: Path) -> Processor:
    ext = path.suffix.lower()
    if ext in {".png", ".jpg", ".jpeg"}:
        return ImageProcessor()
    return TextProcessor()
