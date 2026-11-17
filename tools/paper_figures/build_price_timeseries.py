#!/usr/bin/env python3
"""Export paper-ready price time-series JPEGs by utility ownership."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_price_models import CPI_U_ANNUAL_2013_100  # noqa: E402


DEFAULT_INPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_price_panel_expanded_2013_2024.csv"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "paper-figures"

YEARS = sorted(CPI_U_ANNUAL_2013_100)
CONSTANT_DOLLAR_YEAR = max(YEARS)
CUSTOMER_CLASSES = ("residential", "commercial", "industrial")
OWNERSHIP_TYPES = ("DOM", "MTC", "COOP")

COLORS = {
    "DOM": "#274C77",
    "MTC": "#D97706",
    "COOP": "#128277",
}
TEXT = "#172B4D"
MUTED = "#5B6573"
GRID = "#D9E0E8"
AXIS = "#A8B2BF"

REGULAR_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "DejaVuSans.ttf",
)
BOLD_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
)


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a common font without making the exporter macOS-only."""
    candidates = BOLD_FONT_CANDIDATES if bold else REGULAR_FONT_CANDIDATES
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def load_medians(input_file: Path) -> dict[tuple[str, str], list[float]]:
    """Return annual median real prices for each class and ownership group."""
    grouped: dict[tuple[str, int, str], list[float]] = defaultdict(list)
    with input_file.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))

    expected_rows = 42 * len(YEARS)
    if len(rows) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} utility-year rows; found {len(rows)}"
        )

    for row in rows:
        year = int(row["year"])
        ownership = row["ownership"]
        if year not in CPI_U_ANNUAL_2013_100 or ownership not in OWNERSHIP_TYPES:
            continue
        inflation_factor = (
            CPI_U_ANNUAL_2013_100[CONSTANT_DOLLAR_YEAR]
            / CPI_U_ANNUAL_2013_100[year]
        )
        for customer_class in CUSTOMER_CLASSES:
            raw_value = row[f"{customer_class}_average_price_cents_kwh"].strip()
            if raw_value:
                grouped[(customer_class, year, ownership)].append(
                    float(raw_value) * inflation_factor
                )

    medians: dict[tuple[str, str], list[float]] = {}
    for customer_class in CUSTOMER_CLASSES:
        for ownership in OWNERSHIP_TYPES:
            series = []
            for year in YEARS:
                values = grouped[(customer_class, year, ownership)]
                if not values:
                    raise ValueError(
                        f"No {customer_class} observations for {ownership} in {year}"
                    )
                series.append(statistics.median(values))
            medians[(customer_class, ownership)] = series
    return medians


def rounded_limits(values: list[float]) -> tuple[int, int]:
    low = math.floor((min(values) - 2) / 5) * 5
    high = math.ceil((max(values) + 2) / 5) * 5
    return max(0, low), high


def draw_marker(
    draw: ImageDraw.ImageDraw,
    point: tuple[float, float],
    ownership: str,
    scale: int,
) -> None:
    x, y = point
    radius = 5 * scale
    fill = COLORS[ownership]
    outline = "#FFFFFF"
    width = max(2, scale)
    if ownership == "DOM":
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=fill,
            outline=outline,
            width=width,
        )
    elif ownership == "MTC":
        draw.rectangle(
            (x - radius, y - radius, x + radius, y + radius),
            fill=fill,
            outline=outline,
            width=width,
        )
    else:
        draw.polygon(
            [
                (x, y - radius - 1),
                (x - radius - 1, y + radius),
                (x + radius + 1, y + radius),
            ],
            fill=fill,
            outline=outline,
        )


def draw_legend(
    draw: ImageDraw.ImageDraw,
    start_x: int,
    y: int,
    scale: int,
) -> None:
    label_font = font(15 * scale)
    x = start_x
    for ownership in OWNERSHIP_TYPES:
        draw.line(
            (x, y, x + 42 * scale, y),
            fill=COLORS[ownership],
            width=4 * scale,
        )
        draw_marker(draw, (x + 21 * scale, y), ownership, scale)
        draw.text(
            (x + 52 * scale, y - 10 * scale),
            ownership,
            font=label_font,
            fill=TEXT,
        )
        x += 145 * scale


def draw_panel(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    medians: dict[tuple[str, str], list[float]],
    customer_class: str,
    scale: int,
) -> None:
    left, top, right, bottom = bounds
    tick_font = font(11 * scale)
    axis_font = font(12 * scale)

    plot_left = left + 95 * scale
    plot_right = right - 25 * scale
    plot_top = top
    plot_bottom = bottom - 65 * scale

    all_values = [
        value
        for ownership in OWNERSHIP_TYPES
        for value in medians[(customer_class, ownership)]
    ]
    y_min, y_max = rounded_limits(all_values)

    def x_position(year: int) -> float:
        return plot_left + (year - YEARS[0]) * (plot_right - plot_left) / (
            YEARS[-1] - YEARS[0]
        )

    def y_position(value: float) -> float:
        return plot_bottom - (value - y_min) * (plot_bottom - plot_top) / (
            y_max - y_min
        )

    for tick in range(y_min, y_max + 1, 5):
        y = y_position(tick)
        draw.line((plot_left, y, plot_right, y), fill=GRID, width=scale)
        label = str(tick)
        box = draw.textbbox((0, 0), label, font=tick_font)
        draw.text(
            (plot_left - 14 * scale - (box[2] - box[0]), y - 7 * scale),
            label,
            font=tick_font,
            fill=MUTED,
        )

    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill=AXIS, width=scale)
    draw.line(
        (plot_left, plot_bottom, plot_right, plot_bottom),
        fill=AXIS,
        width=scale,
    )

    for year in YEARS:
        x = x_position(year)
        label = str(year)
        box = draw.textbbox((0, 0), label, font=tick_font)
        draw.text(
            (x - (box[2] - box[0]) / 2, plot_bottom + 16 * scale),
            label,
            font=tick_font,
            fill=MUTED,
        )

    for ownership in OWNERSHIP_TYPES:
        points = [
            (x_position(year), y_position(value))
            for year, value in zip(
                YEARS, medians[(customer_class, ownership)], strict=True
            )
        ]
        draw.line(points, fill=COLORS[ownership], width=4 * scale, joint="curve")
        for point in points:
            draw_marker(draw, point, ownership, scale)

    axis_label = f"{CONSTANT_DOLLAR_YEAR} cents per kWh"
    label_box = draw.textbbox((0, 0), axis_label, font=axis_font)
    label_image = Image.new(
        "RGBA",
        (label_box[2] + 12 * scale, label_box[3] + 12 * scale),
        (255, 255, 255, 0),
    )
    label_draw = ImageDraw.Draw(label_image)
    label_draw.text((4 * scale, 2 * scale), axis_label, font=axis_font, fill=TEXT)
    rotated = label_image.rotate(90, expand=True)
    y_center = (plot_top + plot_bottom) // 2
    image.alpha_composite(
        rotated,
        (left + 8 * scale, int(y_center - rotated.height / 2)),
    )

    x_label = "Year"
    x_box = draw.textbbox((0, 0), x_label, font=axis_font)
    draw.text(
        (
            (plot_left + plot_right - (x_box[2] - x_box[0])) / 2,
            bottom - 18 * scale,
        ),
        x_label,
        font=axis_font,
        fill=TEXT,
    )


def build_individual_figure(
    medians: dict[tuple[str, str], list[float]],
    customer_class: str,
    output_dir: Path,
) -> Path:
    scale = 2
    width, height = 1200 * scale, 680 * scale
    image = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(image)

    draw_legend(draw, 70 * scale, 55 * scale, scale)
    draw_panel(
        image,
        draw,
        (70 * scale, 125 * scale, 1150 * scale, 650 * scale),
        medians,
        customer_class,
        scale,
    )

    output = output_dir / f"price-timeseries-{customer_class}.jpg"
    image.convert("RGB").save(
        output,
        "JPEG",
        quality=95,
        optimize=True,
        dpi=(300, 300),
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-file",
        type=Path,
        default=DEFAULT_INPUT,
        help="processed 42-utility price panel",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="directory for generated JPEGs",
    )
    args = parser.parse_args()

    input_file = args.input_file.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    medians = load_medians(input_file)
    for customer_class in CUSTOMER_CLASSES:
        output = build_individual_figure(medians, customer_class, output_dir)
        print(output)


if __name__ == "__main__":
    main()
