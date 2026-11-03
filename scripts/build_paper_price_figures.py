"""Build paper-ready price time-series JPEGs by utility ownership.

The figures show unweighted annual medians across utilities with a published
EIA bundled-service price. Prices are converted to constant 2024 cents/kWh
using the same CPI-U series as the ownership price models.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "utility_price_panel_expanded_2013_2024.csv"
OUTPUT_DIR = PROJECT_ROOT / "site" / "downloads"

YEARS = list(range(2013, 2025))
CUSTOMER_CLASSES = ("residential", "commercial", "industrial")
OWNERSHIP_TYPES = ("DOM", "MTC", "COOP")

# BLS annual CPI-U, all items, U.S. city average, rebased to 2013 = 100.
CPI_U_ANNUAL_2013_100 = {
    2013: 100.000,
    2014: 101.622,
    2015: 101.743,
    2016: 103.027,
    2017: 105.221,
    2018: 107.791,
    2019: 109.745,
    2020: 111.098,
    2021: 116.318,
    2022: 125.626,
    2023: 130.797,
    2024: 134.655,
}

COLORS = {
    "DOM": "#274C77",
    "MTC": "#D97706",
    "COOP": "#128277",
}
TEXT = "#172B4D"
MUTED = "#5B6573"
GRID = "#D9E0E8"
AXIS = "#A8B2BF"

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size=size)


def load_medians() -> dict[tuple[str, str], list[float]]:
    grouped: dict[tuple[str, int, str], list[float]] = defaultdict(list)
    with INPUT_FILE.open(newline="") as source:
        rows = list(csv.DictReader(source))

    if len(rows) != 504:
        raise ValueError(f"Expected 504 utility-year rows; found {len(rows)}")

    for row in rows:
        year = int(row["year"])
        ownership = row["ownership"]
        if year not in CPI_U_ANNUAL_2013_100 or ownership not in OWNERSHIP_TYPES:
            continue
        inflation_factor = CPI_U_ANNUAL_2013_100[2024] / CPI_U_ANNUAL_2013_100[year]
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


def draw_marker(draw: ImageDraw.ImageDraw, point: tuple[float, float], ownership: str, scale: int) -> None:
    x, y = point
    radius = 5 * scale
    fill = COLORS[ownership]
    outline = "#FFFFFF"
    width = max(2, scale)
    if ownership == "DOM":
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline=outline, width=width)
    elif ownership == "MTC":
        draw.rectangle((x - radius, y - radius, x + radius, y + radius), fill=fill, outline=outline, width=width)
    else:
        draw.polygon(
            [(x, y - radius - 1), (x - radius - 1, y + radius), (x + radius + 1, y + radius)],
            fill=fill,
            outline=outline,
        )


def draw_legend(draw: ImageDraw.ImageDraw, start_x: int, y: int, scale: int) -> None:
    label_font = font(15 * scale)
    x = start_x
    for ownership in OWNERSHIP_TYPES:
        draw.line((x, y, x + 42 * scale, y), fill=COLORS[ownership], width=4 * scale)
        draw_marker(draw, (x + 21 * scale, y), ownership, scale)
        draw.text((x + 52 * scale, y - 10 * scale), ownership, font=label_font, fill=TEXT)
        x += 145 * scale


def draw_panel(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    medians: dict[tuple[str, str], list[float]],
    customer_class: str,
    scale: int,
    show_x_label: bool,
    show_panel_title: bool = True,
) -> None:
    left, top, right, bottom = bounds
    title_font = font(17 * scale, bold=True)
    tick_font = font(11 * scale)
    axis_font = font(12 * scale)
    if show_panel_title:
        draw.text((left, top - 42 * scale), customer_class.title(), font=title_font, fill=TEXT)

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
        return plot_left + (year - YEARS[0]) * (plot_right - plot_left) / (YEARS[-1] - YEARS[0])

    def y_position(value: float) -> float:
        return plot_bottom - (value - y_min) * (plot_bottom - plot_top) / (y_max - y_min)

    for tick in range(y_min, y_max + 1, 5):
        y = y_position(tick)
        draw.line((plot_left, y, plot_right, y), fill=GRID, width=1 * scale)
        label = str(tick)
        box = draw.textbbox((0, 0), label, font=tick_font)
        draw.text((plot_left - 14 * scale - (box[2] - box[0]), y - 7 * scale), label, font=tick_font, fill=MUTED)

    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill=AXIS, width=1 * scale)
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=AXIS, width=1 * scale)

    for year in YEARS:
        x = x_position(year)
        label = str(year)
        box = draw.textbbox((0, 0), label, font=tick_font)
        draw.text((x - (box[2] - box[0]) / 2, plot_bottom + 16 * scale), label, font=tick_font, fill=MUTED)

    for ownership in OWNERSHIP_TYPES:
        points = [
            (x_position(year), y_position(value))
            for year, value in zip(YEARS, medians[(customer_class, ownership)])
        ]
        draw.line(points, fill=COLORS[ownership], width=4 * scale, joint="curve")
        for point in points:
            draw_marker(draw, point, ownership, scale)

    axis_label = "2024 cents per kWh"
    label_box = draw.textbbox((0, 0), axis_label, font=axis_font)
    label_image = Image.new("RGBA", (label_box[2] + 12 * scale, label_box[3] + 12 * scale), (255, 255, 255, 0))
    label_draw = ImageDraw.Draw(label_image)
    label_draw.text((4 * scale, 2 * scale), axis_label, font=axis_font, fill=TEXT)
    rotated = label_image.rotate(90, expand=True)
    y_center = (plot_top + plot_bottom) // 2
    draw._image.alpha_composite(rotated, (left + 8 * scale, int(y_center - rotated.height / 2)))

    if show_x_label:
        x_label = "Year"
        x_box = draw.textbbox((0, 0), x_label, font=axis_font)
        draw.text(((plot_left + plot_right - (x_box[2] - x_box[0])) / 2, bottom - 18 * scale), x_label, font=axis_font, fill=TEXT)


def build_individual_figure(medians, customer_class: str) -> None:
    scale = 2
    width, height = 1200 * scale, 680 * scale
    image = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(image)

    draw_legend(draw, 70 * scale, 55 * scale, scale)
    draw_panel(
        draw,
        (70 * scale, 125 * scale, 1150 * scale, 650 * scale),
        medians,
        customer_class,
        scale,
        show_x_label=True,
        show_panel_title=False,
    )

    output = OUTPUT_DIR / f"figure-price-time-series-{customer_class}.jpg"
    image.convert("RGB").save(output, "JPEG", quality=95, optimize=True, dpi=(300, 300))
    print(output)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    medians = load_medians()
    for customer_class in CUSTOMER_CLASSES:
        build_individual_figure(medians, customer_class)


if __name__ == "__main__":
    main()
