from PIL import Image, ImageDraw

BG = (18, 21, 27, 255)      # --bg
PANEL = (26, 30, 38, 255)   # --panel
AMBER = (255, 176, 32, 255) # --amber
REC = (255, 59, 48, 255)    # --rec

SIZE = 256


def build():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # rounded square backdrop
    pad = 8
    draw.rounded_rectangle([pad, pad, SIZE - pad, SIZE - pad], radius=44, fill=BG)

    # inner panel
    inset = 34
    draw.rounded_rectangle([inset, inset, SIZE - inset, SIZE - inset], radius=20, fill=PANEL)

    # rec dot, top-left of panel
    dot_r = 10
    dot_cx, dot_cy = inset + 26, inset + 26
    draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=REC)

    # amber play triangle, centered lower
    cx, cy = SIZE // 2 + 6, SIZE // 2 + 14
    s = 46
    draw.polygon(
        [(cx - s * 0.55, cy - s), (cx - s * 0.55, cy + s), (cx + s * 0.9, cy)],
        fill=AMBER,
    )

    return img


if __name__ == "__main__":
    icon = build()
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon.save("app_icon.ico", sizes=sizes)
    icon.save("static/app_icon.png")
    print("wrote app_icon.ico and static/app_icon.png")
