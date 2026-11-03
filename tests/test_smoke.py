import pandas as pd
import pytest

from app.analyzer import analyze_text, filter_by_text
from app.dashboard import build_investigation_report, build_relationship_graph, explain_record
from app.data_loader import REQUIRED_COLUMNS, validate_dataset

def test_phishing_terms_are_flagged():
    result = analyze_text("Please verify your account password")
    assert "phishing" in result["risk_labels"]
    assert result["risk_score"] >= 30

def test_normal_text_has_no_rule_match():
    result = analyze_text("The library is open today")
    assert result["risk_labels"] == ["no_rule_match"]

def test_text_filter_treats_special_characters_literally():
    df = pd.DataFrame({
        "text": ["square [ bracket", "round ( bracket", "asterisk * mark", "period . mark", "plain text"]
    })

    for query, expected in [
        ("[", "square [ bracket"),
        ("(", "round ( bracket"),
        ("*", "asterisk * mark"),
        (".", "period . mark"),
    ]:
        filtered = filter_by_text(df, query)
        assert filtered["text"].tolist() == [expected]

def test_empty_text_filter_returns_all_rows():
    df = pd.DataFrame({"text": ["one", "two"]})

    assert filter_by_text(df, "").equals(df)
    assert filter_by_text(df, None).equals(df)

def test_validate_dataset_accepts_valid_records():
    df = pd.DataFrame({
        "post_id": ["SYN-001"],
        "timestamp": ["2026-11-01 09:15:00"],
        "platform": ["DemoFeed"],
        "text": ["A synthetic sample post"],
        "engagement": [42],
        "source_type": ["synthetic"],
    })

    result = validate_dataset(df)

    assert result.warnings == []
    assert len(result.data) == 1
    assert result.data.loc[0, "timestamp"] == pd.Timestamp("2026-11-01 09:15:00")
    assert result.data.loc[0, "validation_issues"] == []

def test_validate_dataset_reports_invalid_records_without_dropping_them():
    df = pd.DataFrame({
        "post_id": ["DUP-1", "DUP-1", "  ", "SYN-004"],
        "timestamp": ["2026-11-01 09:15:00", "not-a-date", "2026-11-01", "2026-11-02"],
        "platform": ["DemoFeed"] * 4,
        "text": ["first post", "   ", "missing ID", "last post"],
        "engagement": [42, "not-a-number", -1, 12.5],
        "source_type": ["synthetic"] * 4,
    })

    result = validate_dataset(df)

    assert len(result.data) == len(df)
    assert result.data.loc[1, "timestamp_original"] == "not-a-date"
    assert result.data.loc[1, "engagement"] == "not-a-number"
    assert result.data.loc[2, "post_id"] == "  "
    assert any("Missing post IDs in records: 3" in warning for warning in result.warnings)
    assert any("Empty text in records: 2" in warning for warning in result.warnings)
    assert any("'DUP-1' (records 1, 2)" in warning for warning in result.warnings)
    assert any("record 2 ('not-a-date')" in warning for warning in result.warnings)
    assert any("record 2 ('not-a-number')" in warning for warning in result.warnings)
    assert any("record 3 (-1)" in warning for warning in result.warnings)
    assert any("record 4 (12.5)" in warning for warning in result.warnings)
    assert result.data.loc[0, "validation_issues"] == [
        "Duplicate post ID: DUP-1"
    ]
    assert result.data.loc[1, "validation_issues"] == [
        "Empty text",
        "Duplicate post ID: DUP-1",
        "Invalid or missing timestamp",
        "Missing or invalid engagement value",
    ]

def test_validate_dataset_rejects_missing_required_columns():
    df = pd.DataFrame({"post_id": ["SYN-001"]})

    with pytest.raises(ValueError, match="missing required columns"):
        validate_dataset(df)

def test_investigation_report_uses_analyzer_evidence_and_marks_review_pending():
    row = {
        "post_id": "SYN-001",
        "risk_labels": ["phishing"],
        "evidence": ["password"],
        "risk_score": 40,
    }

    report = build_investigation_report(row, "Review suspicious login content")

    assert report["objective"] == "Review suspicious login content"
    assert report["findings"] == "Local keyword rules matched phishing."
    assert report["supporting_record_ids"] == ["SYN-001"]
    assert report["evidence"] == ["password"]
    assert report["human_review_status"] == "Pending human review"
    assert "not a probability or proof" in report["uncertainty"]
    assert explain_record(row) == (
        "Matched phishing rule(s) using the observed term(s): password."
    )

def test_network_graph_contains_only_record_platform_and_rule_links():
    df = pd.DataFrame({
        "post_id": ["SYN-001", "SYN-002"],
        "platform": ["DemoFeed", "DemoFeed"],
        "risk_labels": [["phishing"], ["no_rule_match"]],
    })

    graph = build_relationship_graph(df)

    assert graph.nodes["record:0"]["label"] == "SYN-001"
    assert graph.nodes["platform:DemoFeed"]["kind"] == "platform"
    assert graph.nodes["indicator:phishing"]["kind"] == "indicator"
    assert graph.edges["record:0", "platform:DemoFeed"]["relationship"] == "observed platform"
    assert graph.edges["record:0", "indicator:phishing"]["relationship"] == "matched rule"
    assert graph.number_of_edges() == 3
    assert not graph.has_edge("record:0", "record:1")
