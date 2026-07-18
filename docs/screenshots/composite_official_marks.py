#!/usr/bin/env python3
"""Replace AI-redrawn third-party logos with generic icons + plain word marks.

Does NOT paste GitHub / Jenkins / Terraform / AWS brand artwork.
Loads pristine Image2 PNGs from --source-dir (required for clean wipes).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCREENSHOTS = Path(__file__).resolve().parent


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def cover_rect(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int, int],
    radius: int = 6,
) -> None:
    ImageDraw.Draw(canvas).rounded_rectangle(box, radius=radius, fill=fill)


def cover_ellipse(
    canvas: Image.Image,
    cx: int,
    cy: int,
    diameter: int,
    fill: tuple[int, int, int, int],
) -> None:
    r = diameter // 2
    ImageDraw.Draw(canvas).ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)


def word_badge(
    canvas: Image.Image,
    cx: int,
    cy: int,
    text: str,
    *,
    fill: tuple[int, int, int, int] = (15, 35, 70, 255),
    fg: tuple[int, int, int, int] = (255, 255, 255, 255),
    pad_x: int = 14,
    pad_y: int = 8,
    size: int = 18,
) -> None:
    d = ImageDraw.Draw(canvas)
    f = font(size)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x0 = cx - tw // 2 - pad_x
    y0 = cy - th // 2 - pad_y
    x1 = cx + tw // 2 + pad_x
    y1 = cy + th // 2 + pad_y
    d.rounded_rectangle((x0, y0, x1, y1), radius=8, fill=fill)
    d.text((cx, cy), text, fill=fg, font=f, anchor="mm")


def generic_git_icon(canvas: Image.Image, cx: int, cy: int, scale: int = 32) -> None:
    d = ImageDraw.Draw(canvas)
    ink = (20, 40, 70, 255)
    d.line((cx, cy - scale, cx, cy + scale), fill=ink, width=4)
    d.line((cx, cy, cx + scale, cy - scale // 2), fill=ink, width=4)
    for px, py in ((cx, cy - scale), (cx, cy + scale), (cx + scale, cy - scale // 2)):
        d.ellipse((px - 6, py - 6, px + 6, py + 6), fill=ink)


def generic_build_icon(canvas: Image.Image, cx: int, cy: int, scale: int = 30) -> None:
    """Package / build — not Jenkins butler."""
    d = ImageDraw.Draw(canvas)
    ink = (20, 40, 70, 255)
    d.polygon(
        [
            (cx - scale, cy - scale // 3),
            (cx, cy - scale),
            (cx + scale, cy - scale // 3),
            (cx + scale, cy + scale // 2),
            (cx - scale, cy + scale // 2),
        ],
        outline=ink,
        width=3,
    )
    d.line((cx, cy - scale, cx, cy + scale // 2), fill=ink, width=2)
    d.line((cx - scale, cy - scale // 3, cx + scale, cy - scale // 3), fill=ink, width=2)


def generic_blocks_icon(canvas: Image.Image, cx: int, cy: int, scale: int = 22) -> None:
    d = ImageDraw.Draw(canvas)
    ink = (70, 40, 110, 255)
    s = scale
    boxes = [
        (cx - s, cy - s // 3, cx, cy + s // 2),
        (cx, cy - s // 3, cx + s, cy + s // 2),
        (cx - s // 2, cy - s, cx + s // 2, cy - s // 6),
    ]
    for box in boxes:
        d.rectangle(box, outline=ink, width=2)


def generic_hex_box(canvas: Image.Image, cx: int, cy: int, scale: int = 28) -> None:
    """Generic registry/container box — not AWS ECR mark."""
    d = ImageDraw.Draw(canvas)
    ink = (20, 80, 100, 255)
    d.rounded_rectangle(
        (cx - scale, cy - scale, cx + scale, cy + scale),
        radius=6,
        outline=ink,
        width=3,
    )
    d.rectangle((cx - scale // 2, cy - scale // 2, cx + scale // 2, cy + scale // 2), outline=ink, width=2)


def generic_nodes_icon(canvas: Image.Image, cx: int, cy: int, scale: int = 26) -> None:
    """Load-balancer-like nodes — generic."""
    d = ImageDraw.Draw(canvas)
    ink = (20, 80, 100, 255)
    d.ellipse((cx - 6, cy - scale, cx + 6, cy - scale + 12), fill=ink)
    for dx in (-scale, 0, scale):
        d.line((cx, cy - scale + 6, cx + dx, cy + scale // 2), fill=ink, width=2)
        d.ellipse(
            (cx + dx - 5, cy + scale // 2 - 5, cx + dx + 5, cy + scale // 2 + 5),
            fill=ink,
        )


def composite_delivery(src: Path, dst: Path) -> None:
    canvas = load_rgba(src)
    white = (255, 255, 255, 255)
    navy = (10, 30, 60, 255)

    # Card interiors (sampled from Image2) — seamless wipe, no sticker plate
    gh_bg = (236, 239, 241, 255)
    jk_bg = (238, 240, 242, 255)
    stage_bg = (226, 231, 234, 255)

    # GITHUB PR — wipe entire AI Invertocat + teal badge (below navy header)
    cover_rect(canvas, (315, 200, 575, 355), gh_bg, radius=4)
    generic_git_icon(canvas, 445, 255, 28)
    word_badge(canvas, 445, 315, "GitHub", size=16, pad_x=12, pad_y=6)

    # JENKINS — wipe entire AI butler (incl. lower torso); stop above digest hash
    cover_rect(canvas, (905, 200, 1110, 385), jk_bg, radius=4)
    generic_build_icon(canvas, 1000, 260, 28)
    word_badge(canvas, 1000, 325, "Jenkins", size=16, pad_x=12, pad_y=6)

    # AWS smile/cloud → word only on staging band fill
    cover_rect(canvas, (55, 620, 210, 730), stage_bg, radius=6)
    word_badge(canvas, 132, 675, "AWS", fill=navy, size=20, pad_x=16, pad_y=10)

    # Staging teal redraws → generic + words (same fill as card)
    cover_rect(canvas, (505, 645, 655, 770), stage_bg, radius=4)
    generic_hex_box(canvas, 580, 690, 26)
    word_badge(canvas, 580, 745, "ECR", size=14, pad_x=10, pad_y=4, fill=(20, 90, 110, 255))

    cover_rect(canvas, (935, 650, 1085, 775), stage_bg, radius=4)
    generic_hex_box(canvas, 1010, 695, 26)
    word_badge(canvas, 1010, 750, "ECS Fargate", size=12, pad_x=8, pad_y=4, fill=(20, 90, 110, 255))

    cover_rect(canvas, (1385, 650, 1535, 775), stage_bg, radius=4)
    generic_nodes_icon(canvas, 1460, 695, 24)
    word_badge(canvas, 1460, 750, "ALB", size=14, pad_x=10, pad_y=4, fill=(20, 90, 110, 255))

    canvas.convert("RGB").save(dst, "PNG", optimize=True)
    print(f"wrote {dst}")


def composite_phase9(src: Path, dst: Path) -> None:
    canvas = load_rgba(src)
    white = (255, 255, 255, 255)

    # Step 1 GitHub
    cover_rect(canvas, (300, 400, 470, 580), white, radius=8)
    generic_git_icon(canvas, 385, 470, 26)
    word_badge(canvas, 385, 535, "GitHub", size=15, pad_x=11, pad_y=5)

    # Step 2 ECR
    cover_rect(canvas, (540, 400, 720, 560), white, radius=8)
    generic_hex_box(canvas, 630, 460, 28)
    word_badge(canvas, 630, 525, "ECR", size=15, pad_x=11, pad_y=5, fill=(20, 90, 110, 255))

    # Sidebar Terraform
    cover_rect(canvas, (1885, 450, 2020, 560), white, radius=4)
    generic_blocks_icon(canvas, 1955, 485, 18)
    word_badge(canvas, 1955, 535, "Terraform", size=12, pad_x=8, pad_y=3, fill=(70, 40, 110, 255))

    # ALB in VPC
    cover_rect(canvas, (730, 530, 850, 640), white, radius=4)
    generic_nodes_icon(canvas, 790, 580, 22)

    # ECS task icons in AZs
    for cx in (720, 920, 1120):
        cover_rect(canvas, (cx - 40, 720, cx + 40, 800), white, radius=4)
        generic_hex_box(canvas, cx, 760, 20)

    # CloudWatch / IAM cards — wipe AI redraws; keep labels via badges
    cover_rect(canvas, (1295, 450, 1410, 560), white, radius=4)
    word_badge(canvas, 1352, 505, "CloudWatch", size=11, pad_x=7, pad_y=3, fill=(140, 40, 90, 255))
    cover_rect(canvas, (1295, 610, 1410, 720), white, radius=4)
    word_badge(canvas, 1352, 665, "IAM", size=14, pad_x=10, pad_y=4, fill=(140, 50, 50, 255))

    # Sidebar Fargate / ALB
    cover_rect(canvas, (1910, 575, 2010, 665), white, radius=4)
    generic_hex_box(canvas, 1960, 610, 18)
    word_badge(canvas, 1960, 650, "Fargate", size=11, pad_x=7, pad_y=3, fill=(20, 90, 110, 255))
    cover_rect(canvas, (1910, 695, 2010, 785), white, radius=4)
    generic_nodes_icon(canvas, 1960, 730, 16)
    word_badge(canvas, 1960, 770, "ALB", size=11, pad_x=7, pad_y=3, fill=(20, 90, 110, 255))

    canvas.convert("RGB").save(dst, "PNG", optimize=True)
    print(f"wrote {dst}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, required=True)
    args = ap.parse_args()
    src = args.source_dir

    composite_delivery(
        src / "project-c-delivery-infographic.png",
        SCREENSHOTS / "project-c-delivery-infographic.png",
    )
    composite_phase9(
        src / "phase9-architecture.png",
        SCREENSHOTS / "phase9-architecture.png",
    )


if __name__ == "__main__":
    main()
