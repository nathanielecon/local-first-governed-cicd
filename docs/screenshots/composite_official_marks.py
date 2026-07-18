#!/usr/bin/env python3
"""Composite unmodified official brand marks onto CI/CD portfolio PNGs.

Replaces AI-redrawn third-party logos with files from docs/brand/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCREENSHOTS = Path(__file__).resolve().parent
BRAND = SCREENSHOTS.parent / "brand"


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def cover_ellipse(
    canvas: Image.Image, cx: int, cy: int, diameter: int, fill: tuple[int, int, int, int]
) -> None:
    d = ImageDraw.Draw(canvas)
    r = diameter // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)


def cover_rect(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int, int],
    radius: int = 4,
) -> None:
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle(box, radius=radius, fill=fill)


def paste_mark(
    canvas: Image.Image,
    mark: Image.Image,
    cx: int,
    cy: int,
    size: int,
    *,
    max_h: int | None = None,
) -> None:
    m = mark.convert("RGBA").copy()
    if max_h:
        m.thumbnail((size, max_h), Image.Resampling.LANCZOS)
    else:
        m.thumbnail((size, size), Image.Resampling.LANCZOS)
    x0 = cx - m.size[0] // 2
    y0 = cy - m.size[1] // 2
    canvas.alpha_composite(m, (x0, y0))


def paste_aws_icon(
    canvas: Image.Image,
    mark: Image.Image,
    cx: int,
    cy: int,
    size: int,
    *,
    cover_box: tuple[int, int, int, int] | None = None,
) -> None:
    m = mark.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    x0 = cx - size // 2
    y0 = cy - size // 2
    box = cover_box or (x0, y0, x0 + size, y0 + size)
    cover_rect(canvas, box, (255, 255, 255, 255), radius=4)
    canvas.alpha_composite(m, (x0, y0))


def draw_aws_wordmark(
    canvas: Image.Image, box: tuple[int, int, int, int], bg: tuple[int, int, int, int]
) -> None:
    cover_rect(canvas, box, bg, radius=10)
    d = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
        )
    except OSError:
        font = ImageFont.load_default()
    d.text((cx, cy), "AWS", fill=(255, 255, 255, 255), font=font, anchor="mm")


def composite_delivery(src: Path, dst: Path) -> None:
    canvas = load_rgba(src)
    white = (255, 255, 255, 255)
    navy = (10, 30, 60, 255)

    gh = load_rgba(BRAND / "github-mark-black.png")
    jenkins = load_rgba(BRAND / "jenkins.png")
    ecr = load_rgba(BRAND / "aws" / "ecr.png")
    ecs = load_rgba(BRAND / "aws" / "ecs.png")
    fargate = load_rgba(BRAND / "aws" / "fargate.png")
    elb = load_rgba(BRAND / "aws" / "elb.png")

    # GITHUB PR card — wipe card body icon area, then official Invertocat
    cover_rect(canvas, (330, 210, 560, 345), white, radius=6)
    paste_mark(canvas, gh, 445, 275, 90)

    # JENKINS BUILDS ONCE — wipe butler area (keep package icon to the right)
    cover_rect(canvas, (910, 205, 1095, 360), white, radius=8)
    paste_mark(canvas, jenkins, 995, 280, 120, max_h=135)

    # AWS smile/cloud redraw → plain text wordmark
    draw_aws_wordmark(canvas, (80, 635, 200, 720), navy)

    # Staging: cover full teal hex/circle then official Architecture Icons
    paste_aws_icon(canvas, ecr, 580, 705, 72, cover_box=(510, 635, 650, 775))
    paste_aws_icon(canvas, fargate, 1010, 710, 72, cover_box=(940, 640, 1080, 780))
    paste_aws_icon(canvas, elb, 1459, 710, 72, cover_box=(1389, 640, 1529, 780))

    canvas.convert("RGB").save(dst, "PNG", optimize=True)
    print(f"wrote {dst}")


def composite_phase9(src: Path, dst: Path) -> None:
    canvas = load_rgba(src)
    white = (255, 255, 255, 255)

    gh = load_rgba(BRAND / "github-mark-black.png")
    tf = load_rgba(BRAND / "terraform-mark.png")
    ecr = load_rgba(BRAND / "aws" / "ecr.png")
    ecs = load_rgba(BRAND / "aws" / "ecs.png")
    fargate = load_rgba(BRAND / "aws" / "fargate.png")
    elb = load_rgba(BRAND / "aws" / "elb.png")
    iam = load_rgba(BRAND / "aws" / "iam.png")
    cw = load_rgba(BRAND / "aws" / "cloudwatch.png")

    # Step 1 GitHub card — cover AI Invertocat fully
    cover_ellipse(canvas, 380, 490, 130, white)
    paste_mark(canvas, gh, 380, 490, 84)

    # Sidebar step 3 Terraform → official mark
    cover_rect(canvas, (1900, 460, 2010, 555), white, radius=4)
    paste_mark(canvas, tf, 1960, 505, 56)

    # Step 2 Amazon ECR card
    paste_aws_icon(canvas, ecr, 620, 470, 72, cover_box=(560, 410, 680, 530))

    # ALB in VPC flow (approx from architecture layout)
    paste_aws_icon(canvas, elb, 780, 580, 56, cover_box=(740, 540, 820, 620))

    # ECS task icons in AZs
    for cx in (720, 920, 1120):
        paste_aws_icon(canvas, ecs, cx, 760, 52, cover_box=(cx - 32, 728, cx + 32, 792))

    # CloudWatch Logs + IAM cards (right of VPC)
    paste_aws_icon(canvas, cw, 1350, 500, 52, cover_box=(1310, 460, 1390, 540))
    paste_aws_icon(canvas, iam, 1350, 660, 52, cover_box=(1310, 620, 1390, 700))

    # Sidebar Fargate / ALB icons
    paste_aws_icon(canvas, fargate, 1960, 620, 48, cover_box=(1925, 585, 1995, 655))
    paste_aws_icon(canvas, elb, 1960, 740, 48, cover_box=(1925, 705, 1995, 775))

    canvas.convert("RGB").save(dst, "PNG", optimize=True)
    print(f"wrote {dst}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, default=None)
    args = ap.parse_args()
    src = args.source_dir or SCREENSHOTS

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
