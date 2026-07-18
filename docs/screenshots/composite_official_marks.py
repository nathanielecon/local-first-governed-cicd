#!/usr/bin/env python3
"""Wipe AI-drawn third-party logos; keep diagram text as word marks.

Headers already say GitHub / Jenkins / ECR / etc. — do not paste brand artwork
or sticker badges. Only erase logo pixels and optionally draw a simple generic
line icon matching the diagram's navy/teal style.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

SCREENSHOTS = Path(__file__).resolve().parent


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def cover_rect(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int, int],
    radius: int = 4,
) -> None:
    ImageDraw.Draw(canvas).rounded_rectangle(box, radius=radius, fill=fill)


def generic_git_icon(canvas: Image.Image, cx: int, cy: int, scale: int = 32) -> None:
    d = ImageDraw.Draw(canvas)
    ink = (15, 40, 75, 255)
    d.line((cx, cy - scale, cx, cy + scale), fill=ink, width=4)
    d.line((cx, cy, cx + scale, cy - scale // 2), fill=ink, width=4)
    for px, py in ((cx, cy - scale), (cx, cy + scale), (cx + scale, cy - scale // 2)):
        d.ellipse((px - 6, py - 6, px + 6, py + 6), fill=ink)


def generic_package_icon(canvas: Image.Image, cx: int, cy: int, scale: int = 34) -> None:
    d = ImageDraw.Draw(canvas)
    ink = (15, 40, 75, 255)
    d.rectangle((cx - scale, cy - scale // 2, cx + scale, cy + scale // 2), outline=ink, width=3)
    d.line((cx - scale, cy - scale // 6, cx + scale, cy - scale // 6), fill=ink, width=2)
    d.line((cx, cy - scale // 2, cx, cy + scale // 2), fill=ink, width=2)


def generic_hex_box(canvas: Image.Image, cx: int, cy: int, scale: int = 28) -> None:
    d = ImageDraw.Draw(canvas)
    ink = (15, 90, 110, 255)
    d.rounded_rectangle(
        (cx - scale, cy - scale, cx + scale, cy + scale),
        radius=6,
        outline=ink,
        width=3,
    )
    d.rectangle(
        (cx - scale // 2, cy - scale // 2, cx + scale // 2, cy + scale // 2),
        outline=ink,
        width=2,
    )


def generic_nodes_icon(canvas: Image.Image, cx: int, cy: int, scale: int = 26) -> None:
    d = ImageDraw.Draw(canvas)
    ink = (15, 90, 110, 255)
    d.ellipse((cx - 6, cy - scale, cx + 6, cy - scale + 12), fill=ink)
    for dx in (-scale, 0, scale):
        d.line((cx, cy - scale + 6, cx + dx, cy + scale // 2), fill=ink, width=2)
        d.ellipse(
            (cx + dx - 5, cy + scale // 2 - 5, cx + dx + 5, cy + scale // 2 + 5),
            fill=ink,
        )


def generic_blocks_icon(canvas: Image.Image, cx: int, cy: int, scale: int = 20) -> None:
    d = ImageDraw.Draw(canvas)
    ink = (15, 40, 75, 255)
    s = scale
    for box in (
        (cx - s, cy - s // 3, cx, cy + s // 2),
        (cx, cy - s // 3, cx + s, cy + s // 2),
        (cx - s // 2, cy - s, cx + s // 2, cy - s // 6),
    ):
        d.rectangle(box, outline=ink, width=2)


def composite_delivery(src: Path, dst: Path) -> None:
    canvas = load_rgba(src)
    gh_bg = (237, 240, 241, 255)
    jk_bg = (236, 239, 241, 255)
    stage_bg = (226, 231, 234, 255)

    # Wipe AI Invertocat — header already says GITHUB PR
    cover_rect(canvas, (315, 200, 575, 355), gh_bg, radius=2)
    generic_git_icon(canvas, 445, 275, 30)

    # Wipe AI butler entirely (incl. gloves/torso) — stop above IMAGE DIGEST
    cover_rect(canvas, (895, 195, 1120, 405), jk_bg, radius=2)
    generic_package_icon(canvas, 1005, 295, 34)

    # Wipe AI AWS smile — staging title already names AWS
    cover_rect(canvas, (55, 615, 215, 735), stage_bg, radius=4)

    # Wipe teal AI service marks — labels ECR / ECS FARGATE / ALB remain in text
    cover_rect(canvas, (505, 645, 655, 770), stage_bg, radius=2)
    generic_hex_box(canvas, 580, 705, 28)

    cover_rect(canvas, (935, 650, 1085, 775), stage_bg, radius=2)
    generic_hex_box(canvas, 1010, 710, 28)

    cover_rect(canvas, (1385, 650, 1535, 775), stage_bg, radius=2)
    generic_nodes_icon(canvas, 1460, 710, 26)

    canvas.convert("RGB").save(dst, "PNG", optimize=True)
    print(f"wrote {dst}")


def composite_phase9(src: Path, dst: Path) -> None:
    canvas = load_rgba(src)
    white = (255, 255, 255, 255)
    card = (248, 249, 251, 255)

    # GitHub card — wipe Invertocat; "GitHub" text remains below
    cover_rect(canvas, (310, 420, 460, 530), card, radius=2)
    generic_git_icon(canvas, 385, 475, 26)

    # ECR card — wipe AI orange mark
    cover_rect(canvas, (555, 420, 705, 530), card, radius=2)
    generic_hex_box(canvas, 630, 475, 28)

    # Sidebar Terraform mark — wipe; step title already says Terraform
    cover_rect(canvas, (1890, 455, 2015, 555), white, radius=2)
    generic_blocks_icon(canvas, 1955, 505, 18)

    # ALB / ECS / CloudWatch / IAM / sidebar icons — wipe AI marks only
    cover_rect(canvas, (735, 540, 845, 630), card, radius=2)
    generic_nodes_icon(canvas, 790, 585, 20)

    for cx in (720, 920, 1120):
        cover_rect(canvas, (cx - 38, 725, cx + 38, 800), card, radius=2)
        generic_hex_box(canvas, cx, 762, 18)

    cover_rect(canvas, (1300, 460, 1405, 555), card, radius=2)
    cover_rect(canvas, (1300, 620, 1405, 715), card, radius=2)

    cover_rect(canvas, (1915, 580, 2005, 655), white, radius=2)
    generic_hex_box(canvas, 1960, 615, 16)
    cover_rect(canvas, (1915, 700, 2005, 775), white, radius=2)
    generic_nodes_icon(canvas, 1960, 735, 14)

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
