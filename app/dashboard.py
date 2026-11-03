from __future__ import annotations

import networkx as nx
import pandas as pd


def explain_record(row: dict) -> str:
    evidence = row.get("evidence") or []
    labels = row.get("risk_labels") or []
    if not evidence or labels == ["no_rule_match"]:
        return "No configured keyword rule matched this text."
    return (
        f"Matched {', '.join(labels)} rule(s) using the observed term(s): "
        f"{', '.join(evidence)}."
    )


def build_investigation_report(row: dict, objective: str) -> dict:
    labels = row.get("risk_labels") or ["no_rule_match"]
    evidence = row.get("evidence") or []
    flagged = bool(evidence) and labels != ["no_rule_match"]
    return {
        "objective": objective.strip(),
        "findings": (
            f"Local keyword rules matched {', '.join(labels)}."
            if flagged
            else "No configured keyword rule matched this record."
        ),
        "supporting_record_ids": [str(row.get("post_id") or "Unknown record")],
        "evidence": list(evidence),
        "indicator_score": row.get("risk_score", 0),
        "uncertainty": (
            "This is a rule-based triage signal, not a probability or proof. "
            "Keyword matching can miss context, negation, and novel patterns."
        ),
        "human_review_status": "Pending human review",
        "source_label": "Synthetic demo record",
    }


def build_relationship_graph(df: pd.DataFrame) -> nx.Graph:
    graph = nx.Graph()
    for position, row in enumerate(df.to_dict(orient="records")):
        record_node = f"record:{position}"
        post_id = row.get("post_id")
        display_id = str(post_id) if pd.notna(post_id) and str(post_id).strip() else f"Record {position + 1}"
        graph.add_node(
            record_node,
            label=display_id,
            kind="record",
        )

        platform = row.get("platform")
        if pd.notna(platform) and str(platform).strip():
            platform_node = f"platform:{platform}"
            graph.add_node(platform_node, label=str(platform), kind="platform")
            graph.add_edge(record_node, platform_node, relationship="observed platform")

        labels = row.get("risk_labels") or []
        if isinstance(labels, str):
            labels = [labels]
        for label in labels:
            if label and label != "no_rule_match":
                indicator_node = f"indicator:{label}"
                graph.add_node(indicator_node, label=str(label), kind="indicator")
                graph.add_edge(record_node, indicator_node, relationship="matched rule")
    return graph
