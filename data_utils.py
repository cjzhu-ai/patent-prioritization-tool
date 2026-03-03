"""Data helpers for patent CSV: column detection and composite text."""

from typing import Optional

import pandas as pd


def find_column(df: pd.DataFrame, names: list) -> Optional[str]:
    """Return the first column whose name contains any of the given strings (case-insensitive)."""
    for n in names:
        for c in df.columns:
            if n.lower() in c.lower():
                return c
    return None


def get_patent_columns(df: pd.DataFrame) -> dict:
    """
    Detect standard patent columns (abstract, embodiment, claims, title, family).
    Returns dict with keys: abstract, embodiment, claims, title, family (values are column names or None).
    """
    return {
        "abstract": find_column(df, ["abstract"]),
        "embodiment": find_column(df, ["embodiment"]),
        "claims": find_column(df, ["claims"]),
        "title": find_column(df, ["patent_title", "title", "patent title"]),
        "family": find_column(df, ["patent family", "patent_family", "family"]),
    }


# Section labels prefixed to each part of the composite text
_COMPOSITE_SECTIONS = [
    ("abstract", "[abstract]"),
    ("embodiment", "[embodiment]"),
    ("claims", "[claims]"),
    ("title", "[title]"),
]


def build_composite_text(df: pd.DataFrame, columns: dict) -> pd.DataFrame:
    """
    Build composite text per row from columns in order: abstract, embodiment, claims, title.
    Each section is prefixed with [abstract], [embodiment], [claims], [title].
    Adds column _composite_text to a copy of df and returns it.
    """
    col_with_labels = [
        (columns[key], label) for key, label in _COMPOSITE_SECTIONS if columns.get(key)
    ]

    def make_composite(row: pd.Series) -> str:
        parts = []
        for col, label in col_with_labels:
            if col in row.index and pd.notna(row[col]):
                text = str(row[col]).strip()
                if text:
                    parts.append(f"{label}\n{text}")
        return "\n\n".join(parts) if parts else ""

    out = df.copy()
    out["_composite_text"] = df.apply(make_composite, axis=1)
    return out


def row_label_by_title(df: pd.DataFrame, index: int, title_col: Optional[str], max_len: int = 80) -> str:
    """Return a display label for a row (for selectboxes), using title column or fallback to Row i."""
    if not title_col or title_col not in df.columns:
        return f"Row {index}"
    val = df.iloc[index].get(title_col)
    if pd.notna(val) and str(val).strip():
        s = str(val).strip()
        return (s[:max_len] + "...") if len(s) > max_len else s
    return f"Row {index}"
