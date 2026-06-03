from collections import Counter
import re
from pathlib import Path

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
TEXT_EXTS = {".txt", ".docx", ".pdf"}
LOG_EXTS = {".log"}


class WidgetBase:
    label = "Widget"

    def __init__(self, ui):
        self.ui = ui

    @property
    def name(self):
        return self.__class__.__name__

    def action(self):
        if hasattr(self.ui, "_toggle_widget"):
            self.ui._toggle_widget(self.name)
        try:
            self.ui.refresh_results()
        except Exception:
            pass

    def applies_to_row(self, row):
        return False

    def row_display(self, row, iid):
        return {"image": None, "text": ""}


class GalleryWidget(WidgetBase):
    label = "Gallery"

    def applies_to_row(self, row):
        return (row.get("extension") or "").lower() in IMAGE_EXTS

    def row_display(self, row, iid):
        if Image is None or ImageTk is None:
            return {"image": None, "text": ""}
        if not self.applies_to_row(row):
            return {"image": None, "text": ""}

        path = row.get("path")
        if not path:
            return {"image": None, "text": ""}

        try:
            p = Path(path)
            with Image.open(p) as im:
                im.thumbnail((64, 64))
                photo = ImageTk.PhotoImage(im)
                try:
                    self.ui._widget_images[iid] = photo
                except Exception:
                    pass
                return {"image": photo, "text": ""}
        except Exception:
            return {"image": None, "text": ""}


class Top5KeywordsWidget(WidgetBase):
    label = "Top5"

    def applies_to_row(self, row):
        return (row.get("extension") or "").lower() in TEXT_EXTS

    def row_display(self, row, iid):
        if not self.applies_to_row(row):
            return {"image": None, "text": ""}

        content = ""
        try:
            content = self.ui._get_cached_content(row)
        except Exception:
            content = ""

        if not content:
            return {"image": None, "text": ""}

        words = re.findall(r"\w+", content.lower())
        stop = {
            "the",
            "and",
            "of",
            "to",
            "a",
            "in",
            "is",
            "it",
            "for",
            "on",
            "with",
            "as",
            "that",
        }
        words = [w for w in words if w not in stop and len(w) > 2]
        if not words:
            return {"image": None, "text": ""}

        c = Counter(words)
        top5 = c.most_common(5)
        txt = ", ".join(f"{w}:{n}" for w, n in top5)
        return {"image": None, "text": txt}


class AnalyzeLogsWidget(WidgetBase):
    label = "Logs"

    def applies_to_row(self, row):
        return (row.get("extension") or "").lower() in LOG_EXTS

    def row_display(self, row, iid):
        if not self.applies_to_row(row):
            return {"image": None, "text": ""}

        try:
            content = self.ui._get_cached_content(row)
        except Exception:
            content = ""

        if not content:
            return {"image": None, "text": ""}

        errs = len(re.findall(r"\berror\b", content, flags=re.I))
        warns = len(re.findall(r"\bwarn\w*\b", content, flags=re.I))
        infos = len(re.findall(r"\binfo\b", content, flags=re.I))
        parts = []
        if errs:
            parts.append(f"ERR:{errs}")
        if warns:
            parts.append(f"WARN:{warns}")
        if infos:
            parts.append(f"INFO:{infos}")
        if not parts:
            return {"image": None, "text": "(no issues)"}
        return {"image": None, "text": ", ".join(parts)}


class WidgetFactory:

    @staticmethod
    def get_buttons(ui, rows):
        img_count = sum(1 for r in rows if (r.get("extension") or "").lower() in IMAGE_EXTS)
        log_count = sum(1 for r in rows if (r.get("extension") or "").lower() in LOG_EXTS)
        text_count = sum(1 for r in rows if (r.get("extension") or "").lower() in TEXT_EXTS)

        buttons = []
        if img_count >= 4:
            buttons.append(GalleryWidget(ui))
        if log_count >= 4:
            buttons.append(AnalyzeLogsWidget(ui))
        if text_count >= 4:
            buttons.append(Top5KeywordsWidget(ui))

        if not hasattr(ui, "active_widgets"):
            ui.active_widgets = set()

        return buttons

    @staticmethod
    def get_row_display(ui, row, iid):
        if not hasattr(ui, "_widget_images"):
            ui._widget_images = {}

        active = getattr(ui, "active_widgets", set())
        if not active:
            return {"image": None, "text": ""}

        order = [GalleryWidget, Top5KeywordsWidget, AnalyzeLogsWidget]
        for cls in order:
            if cls.__name__ not in active:
                continue
            inst = cls(ui)
            disp = inst.row_display(row, iid)
            if disp and (disp.get("image") or disp.get("text")):
                return {"image": disp.get("image"), "text": disp.get("text", "")}

        return {"image": None, "text": ""}
