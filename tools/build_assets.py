"""Собирает картинки профиля: баннер (тёмный и светлый) и обложки проектов 2:1.

Источник - библиотека картинок D:/Desktop/components/image (только чтение).
Запуск: py -3.14 tools/build_assets.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

LIB = Path("D:/Desktop/components/image")
FONTS = Path("D:/Desktop/components/Les/proto/fonts")
OUT = Path(__file__).resolve().parent.parent / "assets"

BANNER = (1600, 440)
CARD = (800, 400)
RADIUS = 28

THEMES = {
    "dark": {
        "bg": "01 Фоны/Ночные сцены/Фиолетовая ночь/bg-ultra-wide-panorama.webp",
        "focus_y": 0.45,
        "shade": (17, 17, 27),
        "shade_alpha": 235,
        "title": (205, 214, 244),
        "accent": (203, 166, 247),
        "text": (186, 194, 222),
    },
    "light": {
        "bg": "01 Фоны/Светлые/Фиолетовая ночь/bg-paper-cut-layered.webp",
        "focus_y": 0.5,
        "shade": (239, 241, 245),
        "shade_alpha": 200,
        "title": (49, 50, 68),
        "accent": (136, 57, 239),
        "text": (76, 79, 105),
    },
}

MASCOT = "03 Маскоты/Новый стиль/mascot-waving-goodbye-one.webp"

COVERS = {
    # имя: (источник, якорь кадра по x 0..1, по y 0..1, обрезка до кадрирования или None[, яркость])
    "library": ("_docs/screenshots/hero.webp", 0.5, 0.5, (300, 132, 1036, 500)),
    "moon-core": ("06 Иллюстрации/Обложки/cover-moon-core.webp", 0.5, 0.5, None),
    "custom-bg": ("06 Иллюстрации/Обложки/Кот и VS Code.webp", 0.5, 0.5, None, 1.9),
    "network-doctor": (
        "06 Иллюстрации/Обложки/Обложка NetworkDoctor.webp",
        1.0,
        0.5,
        None,
    ),
    "auto-translator": (
        "06 Иллюстрации/Обложки/Обложка AutoTranslator.webp",
        0.85,
        0.5,
        None,
    ),
    "contest-reminder": (
        "06 Иллюстрации/Обложки/Обложка ContestReminder.webp",
        0.9,
        0.5,
        None,
    ),
}


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def cover_crop(im, size, ax=0.5, ay=0.5):
    """Масштабирует с заполнением и обрезает до size; ax/ay - какой край кадра сохранить."""
    w, h = size
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x = round((im.width - w) * ax)
    y = round((im.height - h) * ay)
    return im.crop((x, y, x + w, y + h))


def rounded(im, radius):
    mask = Image.new("L", (im.width * 4, im.height * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, mask.width - 1, mask.height - 1), radius * 4, fill=255
    )
    mask = mask.resize(im.size, Image.LANCZOS)
    im = im.convert("RGBA")
    im.putalpha(mask)
    return im


def left_shade(size, color, alpha):
    """Плавное затемнение (или высветление) слева под текст."""
    w, h = size
    grad = Image.new("L", (w, 1))
    for x in range(w):
        t = x / (w * 0.8)
        grad.putpixel((x, 0), round(alpha * min(1.0, max(0.0, 1.25 - t)) ** 1.3))
    grad = grad.resize(size)
    layer = Image.new("RGBA", size, color + (0,))
    layer.putalpha(grad)
    return layer


def build_banner(theme, t):
    bg = Image.open(LIB / t["bg"]).convert("RGB")
    im = cover_crop(bg, BANNER, 0.5, t["focus_y"]).convert("RGBA")
    im.alpha_composite(left_shade(BANNER, t["shade"], t["shade_alpha"]))

    mascot = Image.open(LIB / MASCOT).convert("RGBA")
    mascot = mascot.resize((400, 400), Image.LANCZOS)
    glow = Image.new("RGBA", mascot.size, (0, 0, 0, 0))
    glow.putalpha(mascot.getchannel("A").point(lambda a: a // 3))
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    mx, my = BANNER[0] - 400 - 70, BANNER[1] - 400 + 10
    im.alpha_composite(glow, (mx + 6, my + 10))
    im.alpha_composite(mascot, (mx, my))

    d = ImageDraw.Draw(im)
    x = 86
    d.text(
        (x, 92), "Привет, я", font=font("Golos-Text_DemiBold.ttf", 40), fill=t["text"]
    )
    d.text((x - 4, 136), "Moon", font=font("Unbounded-Bold.ttf", 118), fill=t["title"])
    bbox = d.textbbox((x - 4, 136), "Moon", font=font("Unbounded-Bold.ttf", 118))
    d.rounded_rectangle((x, bbox[3] + 22, x + 120, bbox[3] + 30), 4, fill=t["accent"])
    body = font("Golos-Text_Regular.ttf", 31)
    y = bbox[3] + 52
    for line in (
        "Делаю инструменты, которые экономят время:",
        "VS Code, картинки с ИИ-помощниками, Unreal, игры и сайты",
    ):
        d.text((x, y), line, font=body, fill=t["text"])
        y += 44

    rounded(im, RADIUS).save(OUT / f"banner-{theme}.webp", quality=90, method=6)


def build_cover(name, src, ax, ay, box, bright=1.0):
    # Новая обложка в общей манере (tools/cover-prompts.md) заменяет временную целиком.
    fresh = f"06 Иллюстрации/Обложки/cover-{name}.webp"
    if (LIB / fresh).exists():
        src, ax, ay, box, bright = fresh, 0.5, 0.5, None, 1.0
    im = Image.open(LIB / src).convert("RGB")
    if box:
        im = im.crop(box)
    if bright != 1.0:
        im = ImageEnhance.Brightness(im).enhance(bright)
    im = cover_crop(im, CARD, ax, ay)
    rounded(im, RADIUS).save(OUT / f"cover-{name}.webp", quality=88, method=6)


# Мелкие картинки для README: маскоты у разделов и ярлыки статуса (обрезка по непрозрачному).
EXTRAS = {
    "mascot-point": ("03 Маскоты/Новый стиль/mascot-pointing-left-whole.webp", 200),
    "mascot-wrench": ("03 Маскоты/Новый стиль/mascot-holding-big-wrench.webp", 200),
    "mascot-joy": ("03 Маскоты/Новый стиль/mascot-jumping-joy-arms.webp", 200),
    "mascot-tea": ("03 Маскоты/Новый стиль/mascot-drinking-tea-big.webp", 200),
    "tag-new": ("02 Наклейки/Ярлыки для README/Фиолетовая ночь/tag-new.webp", 60),
    "tag-beta": ("02 Наклейки/Ярлыки для README/Фиолетовая ночь/tag-beta.webp", 60),
}


def build_extra(name, src, height):
    im = Image.open(LIB / src).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox())
    im = im.resize((round(im.width * height / im.height), height), Image.LANCZOS)
    im.save(OUT / f"{name}.webp", quality=92, method=6)


def build_divider(theme, color):
    """Тонкая линия с растворением к краям и полумесяцем посередине."""
    w, h, s = 1600, 40, 4
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    line = Image.new("L", (w * s, 1))
    for x in range(w * s):
        t = abs(x / (w * s) - 0.5) * 2
        line.putpixel((x, 0), round(255 * max(0.0, 1 - t) ** 1.4))
    band = Image.new("RGBA", (w * s, 3 * s), color + (255,))
    band.putalpha(line.resize((w * s, 3 * s)))
    cy = h * s // 2
    gap = 40 * s
    im.alpha_composite(band, (0, cy - band.height // 2))
    d = ImageDraw.Draw(im)
    d.rectangle((w * s // 2 - gap, 0, w * s // 2 + gap, h * s), fill=(0, 0, 0, 0))
    r = 13 * s
    cx = w * s // 2
    moon = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(moon)
    md.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    md.ellipse((cx - r + 9 * s, cy - r - 3 * s, cx + r + 9 * s, cy + r - 3 * s), fill=0)
    fill = Image.new("RGBA", im.size, color + (255,))
    im.paste(fill, (0, 0), moon)
    im.resize((w, h), Image.LANCZOS).save(OUT / f"divider-{theme}.webp", quality=92, method=6)


def main():
    OUT.mkdir(exist_ok=True)
    for theme, t in THEMES.items():
        build_banner(theme, t)
    for name, spec in COVERS.items():
        build_cover(name, *spec)
    for name, (src, height) in EXTRAS.items():
        build_extra(name, src, height)
    build_divider("dark", (203, 166, 247))
    build_divider("light", (136, 57, 239))
    for f in sorted(OUT.glob("*.webp")):
        print(f.name, f.stat().st_size // 1024, "КБ")


if __name__ == "__main__":
    main()
