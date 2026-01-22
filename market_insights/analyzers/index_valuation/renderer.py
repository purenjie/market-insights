"""Table renderer for index valuation visualization.

This module handles rendering the valuation table as a colored image using matplotlib.
Migrated from index_analysis/index_etf_table.py
"""

from __future__ import annotations

import logging
import textwrap
import time
from pathlib import Path

import matplotlib
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.font_manager as fm

from market_insights.analyzers.index_valuation.models import IndexRow, parse_float

LOG = logging.getLogger(__name__)


def wrap_name(name: str, width: int = 12) -> str:
    """Wrap index name to avoid table crowding.

    Args:
        name: Index name
        width: Maximum width before wrapping

    Returns:
        Wrapped name with newlines
    """
    if len(name) <= width:
        return name
    # Reason: Chinese text doesn't have spaces, wrap by character width
    return "\n".join(textwrap.wrap(name, width=width, break_long_words=True))


def normalize_colors(values: list[float | None]) -> tuple[float, float]:
    """Calculate min/max for color normalization (ignoring None values).

    Args:
        values: List of values to normalize

    Returns:
        Tuple of (min, max) for normalization
    """
    valid = [v for v in values if v is not None]
    if not valid:
        return 0.0, 1.0
    vmin = min(valid)
    vmax = max(valid)
    if vmin == vmax:
        return vmin - 1.0, vmax + 1.0
    return vmin, vmax


def configure_chinese_font() -> None:
    """Configure matplotlib Chinese font to avoid garbled text."""
    # Common Chinese font candidates (by priority)
    candidates = [
        "PingFang SC",
        "Heiti SC",
        "Songti SC",
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Noto Sans CJK",
        "WenQuanYi Micro Hei",
    ]

    selected: str | None = None
    for family in candidates:
        try:
            prop = fm.FontProperties(family=family)
            path = fm.findfont(prop, fallback_to_default=False)
            if path:
                selected = family
                break
        except Exception:
            continue

    if selected is None:
        LOG.warning("No Chinese font found; Chinese characters may not render correctly.")
        return

    matplotlib.rcParams["font.sans-serif"] = [selected]
    matplotlib.rcParams["axes.unicode_minus"] = False
    LOG.info("Using Chinese font family: %s", selected)


class ValuationTableRenderer:
    """Renderer for index valuation table visualization."""

    def __init__(self, dpi: int = 200, output_dir: Path | None = None):
        """Initialize renderer.

        Args:
            dpi: Image resolution (dots per inch)
            output_dir: Output directory for images
        """
        self.dpi = dpi
        self.output_dir = output_dir
        configure_chinese_font()

    def render(self, rows: list[IndexRow], output_path: Path) -> None:
        """Render and save valuation table as image.

        Args:
            rows: List of index rows to render
            output_path: Path to save the image
        """
        # Reason: Must set backend before importing pyplot
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        columns = [
            "指数代码",
            "指数名称",
            "市盈率\nPE TTM",
            "市净率\nPB",
            "股息率%\n(近12个月)",
            "显性\n利率",
            "隐性\n利率",
            "ROE",
            "场内ETF\n代码",
            "年费率",
        ]

        # Build cell text matrix
        cell_text: list[list[str]] = []
        for r in rows:
            r2 = IndexRow(
                security_code=r.security_code,
                name=wrap_name(r.name),
                pe=r.pe,
                pb=r.pb,
                dividend_yield=r.dividend_yield,
                explicit_yield=r.explicit_yield,
                implicit_yield=r.implicit_yield,
                roe=r.roe,
                etf_code=r.etf_code,
                fee_rate=r.fee_rate,
            )
            cell_text.append(r2.as_cells())

        nrows = len(rows)
        # Reason: Height scales with number of rows
        fig_w = 14
        fig_h = max(10, 0.35 * (nrows + 4))
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.axis("off")

        date_str = time.strftime("%Y/%m/%d")
        ax.set_title("指数ETF估值表", fontsize=18, pad=18)
        ax.text(
            0.98, 1.02, date_str, ha="right", va="bottom",
            transform=ax.transAxes, fontsize=12
        )

        table = ax.table(
            cellText=cell_text,
            colLabels=columns,
            cellLoc="center",
            colLoc="center",
            loc="center",
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.0, 1.3)

        self._apply_colors(table, rows)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.tight_layout()
        fig.savefig(output_path, dpi=self.dpi)
        LOG.info("Saved table image: %s", output_path)
        plt.close(fig)

    def _apply_colors(self, table: Any, rows: list[IndexRow]) -> None:
        """Apply conditional coloring to table cells.

        Args:
            table: Matplotlib table object
            rows: List of index rows
        """
        # Prepare data for normalization
        pe_list = [r.pe for r in rows]
        pb_list = [r.pb for r in rows]
        did_list = [r.dividend_yield for r in rows]
        imp_list = [r.implicit_yield for r in rows]
        roe_list = [r.roe for r in rows]
        fee_list = [parse_float(r.fee_rate.replace("%", "")) for r in rows]

        # Create normalizers
        pe_norm = mcolors.Normalize(*normalize_colors(pe_list))
        pb_norm = mcolors.Normalize(*normalize_colors(pb_list))
        did_norm = mcolors.Normalize(*normalize_colors(did_list))
        imp_norm = mcolors.Normalize(*normalize_colors(imp_list))
        roe_norm = mcolors.Normalize(*normalize_colors(roe_list))
        fee_norm = mcolors.Normalize(*normalize_colors(fee_list))

        # Reason: Use new API to avoid deprecation warnings
        cmap_low_green_high_red = matplotlib.colormaps.get_cmap("RdYlGn_r")
        cmap_low_light_high_red = matplotlib.colormaps.get_cmap("YlOrRd")

        header_bg = "#f0f0f0"
        name_bg = "#f7f7f7"

        # Column widths (empirically adjusted)
        col_widths = [0.13, 0.25, 0.08, 0.08, 0.10, 0.08, 0.08, 0.07, 0.10, 0.07]

        for (row_i, col_i), cell in table.get_celld().items():
            cell.set_edgecolor("#333333")
            cell.set_linewidth(0.5)

            # Header row
            if row_i == 0:
                cell.set_facecolor(header_bg)
                cell.set_text_props(weight="bold")
            else:
                # Static column background
                if col_i == 1:
                    cell.set_facecolor(name_bg)

                # Conditional coloring for numeric columns
                idx = row_i - 1
                if col_i == 2 and rows[idx].pe is not None:
                    cell.set_facecolor(cmap_low_green_high_red(pe_norm(rows[idx].pe)))
                elif col_i == 3 and rows[idx].pb is not None:
                    cell.set_facecolor(cmap_low_green_high_red(pb_norm(rows[idx].pb)))
                elif col_i == 4 and rows[idx].dividend_yield is not None:
                    cell.set_facecolor(cmap_low_light_high_red(did_norm(rows[idx].dividend_yield)))
                elif col_i == 5 and rows[idx].explicit_yield is not None:
                    cell.set_facecolor(cmap_low_light_high_red(did_norm(rows[idx].explicit_yield)))
                elif col_i == 6 and rows[idx].implicit_yield is not None:
                    cell.set_facecolor(cmap_low_light_high_red(imp_norm(rows[idx].implicit_yield)))
                elif col_i == 7 and rows[idx].roe is not None:
                    cell.set_facecolor(cmap_low_light_high_red(roe_norm(rows[idx].roe)))
                elif col_i == 9 and fee_list[idx] is not None:
                    cell.set_facecolor(cmap_low_green_high_red(fee_norm(fee_list[idx])))

            # Set column width
            if 0 <= col_i < len(col_widths):
                cell.set_width(col_widths[col_i])
