"""Shared loading/validation helpers for the procurement-component-analyzer scripts.

Centralizes the schema checks described in skill.md so each script can trust
that the columns it touches either exist or have been safely defaulted,
instead of repeating the same checks (and failing with confusing pandas
KeyErrors/AttributeErrors) in every script.
"""
import json
import sys
from pathlib import Path

import pandas as pd

# Columns every script needs regardless of which optional fields are present.
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "supplier_name",
    "component_category",
    "component_criticality",
    "unit_cost_usd",
]

# Optional date columns; parsed (with coercion) only when present.
OPTIONAL_DATE_COLUMNS = ["request_date", "commit_date", "received_date"]

LATE_ARRIVAL_GRACE_DAYS = 5


def _fail(*lines: str) -> None:
    for line in lines:
        print(line)
    sys.exit(1)


def require_columns(df: pd.DataFrame, columns: list, context: str) -> None:
    """Exit with a clear, actionable message if any of `columns` is missing
    from `df`, instead of letting a later df[col] raise a raw KeyError."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        _fail(
            f"Cannot run {context}: missing required column(s): {', '.join(missing)}",
            f"Available columns: {', '.join(df.columns)}",
        )


def _validate_dimension(df: pd.DataFrame, column: str, value, label: str) -> None:
    require_columns(df, [column], f"{label.lower()} lookup")
    available = sorted(df[column].dropna().unique())
    if value not in available:
        _fail(
            f"{label} '{value}' not present in the data.",
            f"Available {label.lower()} values: {', '.join(map(str, available))}",
        )


def validate_filters(df: pd.DataFrame, component=None, supplier=None, criticality=None) -> None:
    """Validate only the dimensions actually provided (None = not filtered on
    that dimension, skip check)."""
    if component is not None:
        _validate_dimension(df, "component_category", component, "Component")
    if supplier is not None:
        _validate_dimension(df, "supplier_name", supplier, "Supplier")
    if criticality is not None:
        _validate_dimension(df, "component_criticality", criticality, "Criticality")


def filter_dataset(df: pd.DataFrame, component=None, supplier=None, criticality=None) -> pd.DataFrame:
    """AND together whichever of component/supplier/criticality were provided.
    Call after validate_filters(). Exits with a clear message if the
    combination matches zero rows."""
    mask = pd.Series(True, index=df.index)
    if component is not None:
        mask &= df["component_category"] == component
    if supplier is not None:
        mask &= df["supplier_name"] == supplier
    if criticality is not None:
        mask &= df["component_criticality"] == criticality
    filtered = df[mask]
    if filtered.empty:
        _fail(
            "No rows match the given filters "
            f"(component={component!r}, supplier={supplier!r}, criticality={criticality!r})."
        )
    return filtered


def parse_date_arg(value: str, flag: str) -> pd.Timestamp:
    """Parse a --startdate/--enddate CLI value (YYYY-MM-DD) into a Timestamp,
    exiting via _fail() if it doesn't parse — shared by any script that
    accepts an order_date range filter."""
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        _fail(f"Could not parse {flag} '{value}' as a date (expected YYYY-MM-DD).")
    return ts


def filter_date_range(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Apply an inclusive order_date range filter. start_date/end_date are
    raw CLI strings (YYYY-MM-DD) or None (no bound on that side). Returns df
    unchanged if both are None. Does not check for an empty result — callers
    already do that themselves after combining this with their other filters."""
    if start_date is None and end_date is None:
        return df
    start_ts = parse_date_arg(start_date, "--startdate") if start_date is not None else None
    end_ts = parse_date_arg(end_date, "--enddate") if end_date is not None else None
    if start_ts is not None and end_ts is not None and start_ts > end_ts:
        _fail(f"--startdate ({start_date}) is after --enddate ({end_date}).")
    out = df
    if start_ts is not None:
        out = out[out["order_date"] >= start_ts]
    if end_ts is not None:
        out = out[out["order_date"] <= end_ts]
    return out


def describe_filters(component=None, supplier=None, criticality=None) -> str:
    """Human-readable label for print headers / chart titles, in place of the
    bare component name used when every script only accepted --component."""
    parts = [
        p for p in [
            f"Component={component}" if component else None,
            f"Supplier={supplier}" if supplier else None,
            f"Criticality={criticality}" if criticality else None,
        ] if p
    ]
    return " | ".join(parts) if parts else "All Data"


def filters_dict(component=None, supplier=None, criticality=None) -> dict:
    """Canonical filters envelope embedded at the top of every JSON export, so
    the scope that produced the file is always self-evident."""
    return {"component": component, "supplier": supplier, "criticality": criticality}


def to_records(df: pd.DataFrame, sort_by: str = None, ascending: bool = False) -> list:
    """Round to 2dp, optionally sort, reset_index, and convert to list-of-dict
    records — the groupby/export boilerplate repeated across breakdown scripts."""
    out = df.round(2)
    if sort_by is not None:
        out = out.sort_values(sort_by, ascending=ascending)
    return json.loads(out.reset_index().to_json(orient="records"))


def require_component_or_supplier(component, supplier, context: str) -> None:
    """For scripts that can run cross-component for one supplier
    (request_commit_actual_gap.py, supplier_scorecard.py): exit unless at
    least one of --component/--supplier was provided. --criticality alone is
    never sufficient to drop the component requirement for these scripts."""
    if component is None and supplier is None:
        _fail(
            f"Cannot run {context}: provide --component, or --supplier (to analyze one supplier across all components).",
            "Optionally narrow further with --criticality in either case.",
        )


def load_dataset(file_path: str, extra_date_cols: list = None) -> pd.DataFrame:
    """Read the CSV, validate the base schema, and fill in/derive optional
    columns so downstream scripts can use them without existence checks.

    extra_date_cols: optional date columns a specific script additionally
    requires to be present (e.g. request_commit_actual_gap.py needs
    request_date/commit_date/received_date to do anything useful) - checked
    up front so the script fails fast with a clear message instead of
    midway through a computation.
    """
    path = Path(file_path)
    if not path.exists():
        _fail(f"File not found: {file_path}")
    if path.suffix.lower() != ".csv":
        _fail(
            f"Expected a .csv file, got: {file_path}",
            "Convert the dataset to CSV before running this script.",
        )

    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        _fail(f"File is empty: {file_path}")
    except pd.errors.ParserError as e:
        _fail(f"Could not parse '{file_path}' as CSV: {e}")

    if df.empty:
        _fail(f"'{file_path}' contains no rows.")

    require_columns(df, REQUIRED_COLUMNS, "this analysis")

    if extra_date_cols:
        require_columns(df, extra_date_cols, "this analysis")

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    if df["order_date"].isna().all():
        _fail("'order_date' column could not be parsed as dates.")

    for col in OPTIONAL_DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # qty_ordered: assume 1 unit per row when missing, per skill.md schema note.
    if "qty_ordered" not in df.columns:
        df["qty_ordered"] = 1
    else:
        df["qty_ordered"] = df["qty_ordered"].fillna(1)

    # line_spend_usd: usually qty * unit price when not supplied directly.
    if "line_spend_usd" not in df.columns:
        df["line_spend_usd"] = df["qty_ordered"] * df["unit_cost_usd"]

    def is_blank(col: str) -> bool:
        """True if the column is absent, or present but entirely empty (a
        header with no data, which some exports leave behind for
        not-yet-populated optional fields)."""
        return col not in df.columns or df[col].isna().all()

    has_commit_received = not is_blank("commit_date") and not is_blank("received_date")

    if is_blank("is_late_arrived"):
        if has_commit_received:
            grace = pd.Timedelta(days=LATE_ARRIVAL_GRACE_DAYS)
            df["is_late_arrived"] = df["received_date"] > (df["commit_date"] + grace)
        else:
            df["is_late_arrived"] = pd.NA

    if is_blank("days_late"):
        if has_commit_received:
            df["days_late"] = (df["received_date"] - df["commit_date"]).dt.days
        else:
            df["days_late"] = float("nan")

    if "has_md_event" not in df.columns:
        df["has_md_event"] = pd.NA

    if is_blank("is_supplier_fault"):
        # Per skill.md: default to True whenever has_md_event is True, unless
        # explicitly stated False.
        df["is_supplier_fault"] = df["has_md_event"].fillna(False)

    if "is_open_late" not in df.columns:
        df["is_open_late"] = pd.NA

    if "cost_of_rework_usd" not in df.columns:
        df["cost_of_rework_usd"] = float("nan")

    if "days_lost_to_md" not in df.columns:
        df["days_lost_to_md"] = float("nan")

    if "md_fault_type" not in df.columns:
        df["md_fault_type"] = pd.NA

    if "project_number" not in df.columns:
        df["project_number"] = pd.NA

    if "quarter" not in df.columns:
        df["quarter"] = pd.NA

    return df
