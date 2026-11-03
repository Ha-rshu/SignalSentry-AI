from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_posts.csv"

REQUIRED_COLUMNS = {"post_id", "timestamp", "platform", "text", "engagement", "source_type"}


@dataclass
class DataValidationResult:
    data: pd.DataFrame
    warnings: list[str]


def _display_value(value: object) -> str:
    if pd.isna(value):
        return "<missing>"
    return repr(value)


def validate_dataset(df: pd.DataFrame) -> DataValidationResult:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Data is missing required columns: {', '.join(sorted(missing))}")

    validated = df.copy()
    row_issues: list[list[str]] = [[] for _ in range(len(validated))]
    warnings: list[str] = []

    def add_issue(mask: pd.Series, message: str) -> list[int]:
        positions = [position for position, flagged in enumerate(mask.tolist()) if flagged]
        for position in positions:
            row_issues[position].append(message)
        return positions

    post_ids = validated["post_id"]
    missing_ids = post_ids.isna() | post_ids.astype("string").str.strip().eq("").fillna(False)
    missing_id_positions = add_issue(missing_ids, "Missing post ID")
    if missing_id_positions:
        records = ", ".join(str(position + 1) for position in missing_id_positions)
        warnings.append(f"Missing post IDs in records: {records}.")

    texts = validated["text"]
    empty_text = texts.isna() | texts.astype("string").str.strip().eq("").fillna(False)
    empty_text_positions = add_issue(empty_text, "Empty text")
    if empty_text_positions:
        records = ", ".join(str(position + 1) for position in empty_text_positions)
        warnings.append(f"Empty text in records: {records}.")

    id_positions: dict[str, list[int]] = {}
    for position, post_id in enumerate(post_ids.astype("string").str.strip().tolist()):
        if pd.notna(post_id) and post_id:
            id_positions.setdefault(str(post_id), []).append(position)
    duplicate_groups = {
        post_id: positions for post_id, positions in id_positions.items()
        if len(positions) > 1
    }
    if duplicate_groups:
        duplicate_details = []
        for post_id, positions in duplicate_groups.items():
            records = ", ".join(str(position + 1) for position in positions)
            duplicate_details.append(f"{post_id!r} (records {records})")
            for position in positions:
                row_issues[position].append(f"Duplicate post ID: {post_id}")
        warnings.append(f"Duplicate post IDs: {'; '.join(duplicate_details)}.")

    original_timestamps = validated["timestamp"].copy()
    parsed_timestamps = pd.to_datetime(original_timestamps, errors="coerce", format="mixed")
    invalid_timestamps = parsed_timestamps.isna()
    invalid_timestamp_positions = add_issue(invalid_timestamps, "Invalid or missing timestamp")
    if invalid_timestamp_positions:
        validated["timestamp_original"] = original_timestamps.where(invalid_timestamps)
        details = ", ".join(
            f"record {position + 1} ({_display_value(original_timestamps.iloc[position])})"
            for position in invalid_timestamp_positions
        )
        warnings.append(f"Invalid or missing timestamps: {details}.")
    validated["timestamp"] = parsed_timestamps

    numeric_engagement = pd.to_numeric(validated["engagement"], errors="coerce")
    valid_engagement = (
        numeric_engagement.notna()
        & numeric_engagement.ge(0)
        & numeric_engagement.mod(1).eq(0)
    )
    invalid_engagement = ~valid_engagement
    invalid_engagement_positions = add_issue(
        invalid_engagement, "Missing or invalid engagement value"
    )
    if invalid_engagement_positions:
        details = ", ".join(
            f"record {position + 1} ({_display_value(validated['engagement'].iloc[position])})"
            for position in invalid_engagement_positions
        )
        warnings.append(f"Missing or invalid engagement values: {details}.")

    validated["validation_issues"] = row_issues
    return DataValidationResult(data=validated, warnings=warnings)


def load_sample_data() -> DataValidationResult:
    return validate_dataset(pd.read_csv(DATA_FILE))
