"""
csv_parser.py — Pandas-based CSV cleaning utility
"""
import io
import logging
from typing import List, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLS = {"name", "roll_number"}
OPTIONAL_COLS = {"email", "branch", "year", "phone"}
ALIASES = {
    "roll_no": "roll_number",
    "roll": "roll_number",
    "student_name": "name",
    "mobile": "phone",
    "department": "branch",
}


def parse_csv(content: bytes) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse and clean a CSV file of students.

    Returns:
        (cleaned_df, errors) — DataFrame with standardized columns, and a list of row-level errors.
    """
    errors: List[str] = []

    # Decode
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    df = pd.read_csv(io.StringIO(text), dtype=str)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Apply column aliases
    df.rename(columns=ALIASES, inplace=True)

    # Drop fully empty rows
    df.dropna(how="all", inplace=True)

    # Validate required columns
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    # Strip whitespace from all string cells
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Remove rows missing required fields
    before = len(df)
    df = df[df["name"].notna() & (df["name"] != "")]
    df = df[df["roll_number"].notna() & (df["roll_number"] != "")]
    dropped = before - len(df)
    if dropped:
        errors.append(f"{dropped} rows dropped: missing name or roll_number")

    # Normalize roll_number to uppercase
    df["roll_number"] = df["roll_number"].str.upper()

    # Keep only known columns
    keep = list(REQUIRED_COLS | OPTIONAL_COLS)
    df = df[[c for c in keep if c in df.columns]]

    # Reset index
    df.reset_index(drop=True, inplace=True)

    logger.info(f"CSV parsed: {len(df)} valid rows, {len(errors)} warnings")
    return df, errors
