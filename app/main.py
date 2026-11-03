from datetime import datetime

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.agent import build_investigation_brief, meta_api_status
from app.analyzer import analyze_dataset, filter_by_text
from app.dashboard import (
    build_investigation_report,
    build_relationship_graph,
    explain_record,
)
from app.data_loader import load_sample_data
from app.ui import (
    PAGES,
    apply_design_system,
    command_shortcut,
    render_alert_card,
    render_empty_state,
    render_hero,
    render_page_heading,
    render_topbar,
    severity_for_score,
    style_figure,
)

st.set_page_config(
    page_title="SignalSentry | Command Center",
    page_icon=":material/security:",
    layout="wide",
)

apply_design_system()

if "command_palette_open" not in st.session_state:
    st.session_state.command_palette_open = False


def _open_command_palette() -> None:
    st.session_state.command_palette_open = True


def _close_command_palette() -> None:
    st.session_state.command_palette_open = False


@st.dialog("Command palette", width="small", on_dismiss=_close_command_palette)
def _show_command_palette() -> None:
    st.caption("Navigate to a SignalSentry workspace.")
    destination = st.selectbox("Go to", PAGES, key="command_palette_destination")
    go_col, close_col = st.columns(2)
    if go_col.button("Open workspace", type="primary"):
        st.session_state.workspace_navigation = destination
        st.session_state.command_palette_open = False
        st.rerun()
    if close_col.button("Close"):
        st.session_state.command_palette_open = False
        st.rerun()


command_shortcut(key="signalsentry_command_shortcut", on_open=_open_command_palette)
if st.session_state.command_palette_open:
    _show_command_palette()

st.sidebar.markdown("### SIGNALSENTRY")
st.sidebar.caption("ANALYST WORKSPACE")
with st.sidebar.popover("Quick switch  ·  Ctrl+K"):
    quick_destination = st.selectbox("Workspace", PAGES, key="quick_switch_destination")
    if st.button("Open workspace", key="quick_switch_open"):
        st.session_state.workspace_navigation = quick_destination
        st.rerun()
page = st.sidebar.radio("Workspace", PAGES, key="workspace_navigation")
st.sidebar.caption("Synthetic records · local rule-based analysis")

try:
    validation = load_sample_data()
    analyzed = analyze_dataset(validation.data)
except Exception as exc:
    st.error(f"Could not load sample data: {exc}")
    st.stop()

configured, api_message = meta_api_status()
if validation.warnings:
    st.warning("Data validation found issues. No records were dropped.")
    with st.expander("Validation details"):
        st.code("\n".join(validation.warnings))

if "investigation_report" not in st.session_state:
    st.session_state.investigation_report = None
if "investigation_history" not in st.session_state:
    st.session_state.investigation_history = []

render_topbar()


def _draw_network(graph: nx.Graph) -> None:
    if graph.number_of_nodes() == 0:
        render_empty_state(
            "No relationships to draw",
            "Change the network filters or check the source records.",
        )
        return

    positions = nx.spring_layout(graph, seed=17)
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for source, target in graph.edges:
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x.extend([float(x0), float(x1), None])
        edge_y.extend([float(y0), float(y1), None])

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1, color="#314762"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    node_colors = {"record": "#55baff", "platform": "#46cfc2", "indicator": "#9baeff"}
    for kind, color in node_colors.items():
        nodes = [node for node, data in graph.nodes(data=True) if data["kind"] == kind]
        if not nodes:
            continue
        figure.add_trace(
            go.Scatter(
                x=[float(positions[node][0]) for node in nodes],
                y=[float(positions[node][1]) for node in nodes],
                mode="markers+text",
                text=[graph.nodes[node]["label"] for node in nodes],
                customdata=[
                    [
                        node,
                        graph.nodes[node]["kind"],
                        ", ".join(sorted(graph.neighbors(node))),
                    ]
                    for node in nodes
                ],
                textposition="top center",
                textfont=dict(size=10, color="#d5e0ed"),
                marker=dict(
                    size=16 if kind == "record" else 13,
                    color=color,
                    line=dict(width=1, color="#edf2ff"),
                    opacity=0.93,
                ),
                name={"record": "Synthetic record", "platform": "Observed platform", "indicator": "Matched rule"}[kind],
                hovertemplate=(
                    "<b>%{text}</b><br>Type: %{customdata[1]}"
                    "<br>Observed connections: %{customdata[2]}<extra></extra>"
                ),
            )
        )
    figure.update_layout(
        showlegend=True,
        height=520,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    selection = st.plotly_chart(
        style_figure(figure),
        key="network_intelligence_graph",
        on_select="rerun",
        selection_mode="points",
    )
    selected_points = selection.selection.points
    if selected_points:
        selected_data = selected_points[0].get("customdata")
        if selected_data:
            selected_node = str(selected_data[0])
            if selected_data[1] == "record":
                st.info(
                    f"Selected synthetic record **{graph.nodes[selected_node]['label']}**. "
                    f"Supported links: {selected_data[2] or 'none'}."
                )
            else:
                st.info(
                    f"Selected **{graph.nodes[selected_node]['label']}** ({selected_data[1]}). "
                    "Connections reflect only fields and configured rule matches."
                )


def _get_report() -> dict | None:
    report = st.session_state.investigation_report
    return report if isinstance(report, dict) else None


def _get_investigation_history() -> list[dict]:
    history = st.session_state.investigation_history
    return history if isinstance(history, list) else []


def _inspect_record(record_id: str) -> None:
    st.session_state.focus_record_id = record_id
    st.session_state.threat_selected_record = record_id
    st.session_state.workspace_navigation = "Threat intelligence"


def _render_report(report: dict) -> None:
    st.subheader("Findings")
    st.write(report["findings"])
    st.metric("Rule-based indicator score", f"{report['indicator_score']}/100")
    st.write("**Supporting synthetic record IDs**")
    st.write(", ".join(report["supporting_record_ids"]))
    st.write("**Matched evidence terms**")
    st.write(", ".join(report["evidence"]) if report["evidence"] else "No configured term matched.")
    st.write("**Uncertainty and limitations**")
    st.caption(report["uncertainty"])
    st.write(f"**Human review status:** {report['human_review_status']}")
    st.caption("Investigation objective is recorded for the analyst; no AI model interprets it.")


if page == "Command center":
    with st.container(key="command-center-hero"):
        hero_col, action_col = st.columns([2.4, 0.8])
        with hero_col:
            render_hero()
        with action_col:
            with st.container(border=True):
                st.badge("LOCAL · SYNTHETIC", color="blue")
                st.markdown("**Ready for analyst review**")
                st.caption("Local rules only. No live AI or feed.")
                st.button(
                    "Start investigation",
                    type="primary",
                    key="hero_start_investigation",
                    on_click=lambda: st.session_state.__setitem__(
                        "workspace_navigation", "Investigation workspace"
                    ),
                )

    suspicious = analyzed.risk_score >= 30
    report = _get_report()
    history = _get_investigation_history()
    quality_label = "Review needed" if validation.warnings else "All checks passed"
    with st.container(horizontal=True):
        st.metric("Records analyzed", len(analyzed), border=True, help="Synthetic records loaded for this session.")
        st.metric("Suspicious indicators", int(suspicious.sum()), border=True, help="Records with a local rule score of 30 or more.")
        st.metric("Investigations completed", len(history), border=True, help="Investigation runs in this browser session.")
        st.metric("Data validation", quality_label, border=True)
    if validation.warnings:
        st.warning("Data validation needs review. No records were dropped.")
    else:
        st.caption("Data validation passed for the bundled synthetic sample.")

    st.subheader("Threat activity")
    st.caption("Counts are calculated from the loaded dataset; no live feed is connected.")
    valid_time = analyzed.loc[analyzed.timestamp.notna()].copy()
    if valid_time.empty:
        with st.container(border=True):
            st.caption("No valid timestamps are available to build an activity trend.")
    else:
        valid_time["day"] = valid_time["timestamp"].dt.floor("D")
        daily = (
            valid_time.groupby("day", as_index=False)
            .agg(records=("post_id", "size"), flagged=("risk_score", lambda scores: int((scores >= 30).sum())))
            .sort_values("day")
        )
        chart_col, severity_col = st.columns([1.45, 0.8])
        with chart_col:
            with st.container(border=True):
                st.markdown("**Daily activity**")
                trend = px.line(
                    daily,
                    x="day",
                    y=["records", "flagged"],
                    markers=True,
                    labels={"day": "Date", "value": "Records", "variable": "Series"},
                )
                trend.update_traces(line=dict(width=2))
                st.plotly_chart(style_figure(trend))
        with severity_col:
            with st.container(border=True):
                st.markdown("**Indicator severity**")
                severity_counts = pd.Series(
                    [severity_for_score(int(score))[0] for score in analyzed.risk_score]
                ).value_counts().reindex(
                    ["HIGH INDICATOR", "REVIEW", "INFORMATIONAL"], fill_value=0
                )
                severity_chart = go.Figure(
                    go.Pie(
                        labels=severity_counts.index,
                        values=severity_counts.values,
                        hole=0.66,
                        sort=False,
                        marker=dict(
                            colors=["#ff737f", "#f3bd68", "#77a9ff"],
                            line=dict(color="#11182a", width=3),
                        ),
                        textinfo="label+value",
                        textposition="outside",
                        hovertemplate="%{label}: %{value} records<extra></extra>",
                    )
                )
                severity_chart.update_layout(
                    showlegend=False,
                    height=290,
                    margin=dict(l=12, r=12, t=16, b=16),
                    uniformtext=dict(minsize=9, mode="hide"),
                    annotations=[
                        dict(
                            text=f"{len(analyzed)}<br><span style='font-size:10px'>records</span>",
                            x=0.5,
                            y=0.5,
                            showarrow=False,
                            font=dict(color="#e6edff", size=16),
                        )
                    ],
                )
                st.plotly_chart(style_figure(severity_chart))

        platform_col, radar_col = st.columns(2)
        with platform_col:
            with st.container(border=True):
                st.markdown("**Platform distribution**")
                platform_counts = analyzed.platform.fillna("Unknown").value_counts()
                platform_chart = px.bar(
                    x=platform_counts.values,
                    y=platform_counts.index,
                    orientation="h",
                    labels={"x": "Records", "y": ""},
                )
                platform_chart.update_layout(showlegend=False)
                st.plotly_chart(style_figure(platform_chart))
        with radar_col:
            with st.container(border=True):
                st.markdown("**Threat radar · demo records**")
                st.caption("Rule-match counts from this synthetic dataset, not a live network feed.")
                rule_counts = analyzed.risk_labels.explode().value_counts()
                radar_categories = [
                    category
                    for category in rule_counts.index.tolist()
                    if category != "no_rule_match"
                ]
                if not radar_categories:
                    render_empty_state("No rule matches", "No configured rule categories appear in this dataset.")
                else:
                    radar = go.Figure(
                        go.Scatterpolar(
                            r=[int(rule_counts[category]) for category in radar_categories],
                            theta=radar_categories,
                            fill="toself",
                            fillcolor="rgba(119, 169, 255, .16)",
                            line=dict(color="#77a9ff", width=2),
                            marker=dict(color="#62e0d1", size=6),
                            hovertemplate="%{theta}: %{r} matched records<extra></extra>",
                        )
                    )
                    radar.update_layout(
                        polar=dict(
                            bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(visible=True, gridcolor="rgba(136,154,195,.18)", color="#a6b1c8"),
                            angularaxis=dict(gridcolor="rgba(136,154,195,.18)", color="#dbe4f3"),
                        ),
                        showlegend=False,
                        height=320,
                    )
                    st.plotly_chart(style_figure(radar))

    st.subheader("Alert intelligence")
    st.caption("Priority labels reflect only the existing heuristic score; they are not validated threat severity.")
    alerts = analyzed.loc[analyzed.risk_score >= 30].sort_values(
        ["risk_score", "timestamp"], ascending=[False, False], na_position="last"
    )
    if alerts.empty:
        render_empty_state(
            "No alerts meet the review threshold",
            "Synthetic records below the existing score threshold remain available in Threat Intelligence.",
        )
    else:
        alert_col, alert_col_2 = st.columns(2)
        for index, (_, alert) in enumerate(alerts.head(4).iterrows()):
            card = alert_col if index % 2 == 0 else alert_col_2
            with card:
                preview = alert.get("text", "")
                if pd.isna(preview):
                    preview = ""
                render_alert_card(
                    alert.post_id,
                    alert.platform,
                    int(alert.risk_score),
                    alert.risk_labels,
                    alert.evidence,
                    str(preview),
                )
                st.button(
                    f"Inspect {alert.post_id}",
                    key=f"inspect_alert_{alert.post_id}",
                    help="Open this record in Threat Intelligence.",
                    on_click=_inspect_record,
                    args=(str(alert.post_id),),
                )

    st.subheader("Recent investigation activity")
    if history:
        recent_activity = pd.DataFrame(
            [
                {
                    "Started": item["started_at"],
                    "Record": item["supporting_record_ids"][0],
                    "Objective": item["objective"] or "Objective not provided",
                    "Review status": item["human_review_status"],
                }
                for item in reversed(history[-5:])
            ]
        )
        st.dataframe(recent_activity, hide_index=True)
    else:
        render_empty_state(
            "No investigations yet",
            "Choose a synthetic sample from the Investigation workspace to create the first report.",
        )
    with st.expander("Recent synthetic records"):
        st.caption("All records are local synthetic examples.")
        recent = analyzed.sort_values("timestamp", ascending=False, na_position="last")
        st.dataframe(
            recent[["timestamp", "platform", "post_id", "risk_score"]],
            hide_index=True,
        )

elif page == "Investigation workspace":
    render_page_heading(
        "Investigation workspace",
        "Set an analyst objective, then inspect one synthetic record with local rules.",
    )
    st.badge("SYNTHETIC DEMO", color="blue")
    st.caption(
        "Local keyword analysis only. The objective is saved as analyst context; no AI model interprets it."
    )
    example_objectives = {
        "Choose an example": "",
        "Review matched evidence terms": "Review the matched terms and categories in this synthetic record.",
        "Check for contextual false positives": "Check whether the matched keywords could be benign in context.",
        "Prepare for human corroboration": "Identify what evidence needs independent analyst corroboration.",
    }
    prompt_col, prompt_button_col = st.columns([1.5, 0.6])
    with prompt_col:
        selected_prompt = st.selectbox(
            "Example objectives",
            list(example_objectives),
            key="investigation_example_prompt",
        )
    with prompt_button_col:
        st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
        st.button(
            "Use example",
            key="use_investigation_example",
            disabled=not example_objectives[selected_prompt],
            on_click=lambda: st.session_state.__setitem__(
                "investigation_objective", example_objectives[selected_prompt]
            ),
        )
    objective = st.text_area(
        "Investigation objective",
        placeholder="For example: Review the evidence terms in this sample record.",
        key="investigation_objective",
    )
    sample_positions = [
        position
        for position, source in enumerate(analyzed.source_type)
        if str(source).strip().lower() == "synthetic"
    ]
    if not sample_positions:
        st.warning("No synthetic records are available for investigation.")
    else:
        selected_position = st.selectbox(
            "Synthetic sample investigation",
            sample_positions,
            format_func=lambda position: (
                f"{analyzed.iloc[position].post_id} · "
                f"{analyzed.iloc[position].platform} · "
                f"indicator {analyzed.iloc[position].risk_score}/100"
            ),
        )
        if st.button("Start investigation", type="primary"):
            selected = analyzed.iloc[selected_position].to_dict()
            report_data = build_investigation_report(selected, objective)
            report_data["brief"] = build_investigation_brief(selected)
            report_data["started_at"] = datetime.now().isoformat(timespec="seconds")
            st.session_state.investigation_report = report_data
            st.session_state.investigation_history = [
                *_get_investigation_history(),
                report_data,
            ][-20:]
            st.success("Local rule analysis complete. Review the evidence and limitations below.")
            st.toast("Evidence-led report created for human review.")
        active_report = _get_report()
        if active_report:
            result_col, context_col = st.columns([1.35, 0.85])
            with result_col:
                with st.container(border=True):
                    st.markdown("**Analysis results**")
                    _render_report(active_report)
            with context_col:
                with st.container(border=True):
                    st.markdown("**Local workflow**")
                    st.markdown(
                        '<div class="ss-timeline">'
                        '<div class="ss-timeline-step">Synthetic record selected</div>'
                        '<div class="ss-timeline-step">Configured keyword rules applied</div>'
                        '<div class="ss-timeline-step">Evidence report prepared</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption("No external tools or AI reasoning are running.")
                with st.expander("Full investigation brief"):
                    st.markdown(active_report["brief"])

elif page == "Threat intelligence":
    render_page_heading(
        "Threat intelligence",
        "Filter synthetic evidence and inspect which observed terms triggered local rules.",
    )
    st.caption("Synthetic records · Findings are keyword indicators for human review, not conclusions.")
    filtered = analyzed.copy()
    platforms = sorted(filtered.platform.dropna().astype(str).unique())
    selected_platforms = st.multiselect("Platform", platforms, default=platforms)
    filtered = filtered[filtered.platform.astype("string").isin(selected_platforms)]

    valid_times = filtered.timestamp.dropna()
    include_undated = st.checkbox("Include records with invalid or missing timestamps", value=True)
    if not valid_times.empty:
        start = valid_times.min().date()
        end = valid_times.max().date()
        date_range = st.date_input("Timestamp range", value=(start, end))
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            in_range = filtered.timestamp.dt.date.between(start_date, end_date)
            if include_undated:
                in_range = in_range | filtered.timestamp.isna()
            filtered = filtered[in_range]
    elif not include_undated:
        filtered = filtered.iloc[0:0]

    evidence_table = filtered.copy()
    evidence_table["matched_indicators"] = evidence_table.risk_labels.map(
        lambda labels: ", ".join(labels) if labels else "No rule match"
    )
    evidence_table["why_flagged"] = evidence_table.apply(
        lambda row: explain_record(row.to_dict()), axis=1
    )
    columns = [
        "post_id",
        "platform",
        "timestamp",
        "risk_score",
        "matched_indicators",
        "evidence",
        "why_flagged",
        "validation_issues",
    ]
    if evidence_table.empty:
        render_empty_state(
            "No records match these filters",
            "Adjust the platform or timestamp range to view synthetic evidence.",
        )
    else:
        st.dataframe(evidence_table[columns], hide_index=True)
        record_ids = evidence_table.post_id.astype(str).tolist()
        focus_record_id = st.session_state.get("focus_record_id")
        if focus_record_id not in record_ids:
            focus_record_id = None
        if (
            "threat_selected_record" in st.session_state
            and st.session_state.threat_selected_record not in record_ids
        ):
            del st.session_state["threat_selected_record"]
        default_index = (
            record_ids.index(focus_record_id)
            if focus_record_id in record_ids
            else 0
        )
        selected_record_id = st.selectbox(
            "Inspect record",
            record_ids,
            index=default_index,
            key="threat_selected_record",
        )
        selected_record = evidence_table.loc[
            evidence_table.post_id.astype(str) == selected_record_id
        ].iloc[0].to_dict()
        with st.container(border=True):
            st.markdown(f"**{selected_record_id} · {selected_record['platform']}**")
            score = int(selected_record["risk_score"])
            if score >= 60:
                st.badge(f"High indicator · {score}/100", color="red")
            elif score >= 30:
                st.badge(f"Review · {score}/100", color="orange")
            else:
                st.badge(f"Informational · {score}/100", color="blue")
            st.write(selected_record["text"])
            st.caption(explain_record(selected_record))
        st.session_state.focus_record_id = None

elif page == "Network intelligence":
    render_page_heading(
        "Network intelligence",
        "Explore only relationships explicitly present in record fields and rule outputs.",
    )
    st.caption(
        "Edges show only record-to-platform fields and record-to-matched-rule outputs. "
        "They do not imply coordination, identity, or a relationship between records."
    )
    platform_options = sorted(analyzed.platform.dropna().astype(str).unique())
    network_platforms = st.multiselect(
        "Platforms",
        platform_options,
        default=platform_options,
        key="network_platform_filter",
    )
    relationship_layers = st.multiselect(
        "Relationship layers",
        ["Observed platforms", "Matched rules"],
        default=["Observed platforms", "Matched rules"],
        key="network_relationship_layers",
    )
    network_records = analyzed[
        analyzed.platform.astype("string").isin(network_platforms)
    ]
    network_graph = build_relationship_graph(network_records)
    visible_kinds = set()
    if "Observed platforms" in relationship_layers:
        visible_kinds.add("platform")
    if "Matched rules" in relationship_layers:
        visible_kinds.add("indicator")
    network_graph.remove_nodes_from(
        [
            node
            for node, attributes in network_graph.nodes(data=True)
            if attributes["kind"] not in visible_kinds | {"record"}
        ]
    )
    graph_col, context_col = st.columns([1.7, 0.8])
    with graph_col:
        _draw_network(network_graph)
    with context_col:
        with st.container(border=True):
            st.markdown("**Relationship model**")
            st.caption("Blue nodes are synthetic records.")
            st.caption("Cyan nodes are source platform fields.")
            st.caption("Violet nodes are analyzer rule labels.")
            st.markdown(
                f"**Records shown:** {network_records.shape[0]}  \n"
                f"**Supported links:** {network_graph.number_of_edges()}"
            )
            st.caption("Select a point in the graph for its observed connection details.")

elif page == "Investigation report":
    render_page_heading(
        "Investigation report",
        "Review findings, supporting synthetic records, uncertainty, and analyst status.",
    )
    history = _get_investigation_history()
    if not history:
        st.info("No report yet. Start an investigation from the Investigation workspace.")
    else:
        selected_report_index = st.selectbox(
            "Recent report",
            list(reversed(range(len(history)))),
            format_func=lambda index: (
                f"{history[index]['supporting_record_ids'][0]} · "
                f"{history[index]['started_at']}"
            ),
        )
        report = history[selected_report_index]
        st.session_state.investigation_report = report
        st.caption(f"{report['source_label']} · Created {report['started_at']}")
        st.write(f"**Objective:** {report['objective'] or 'Not provided'}")
        _render_report(report)
        if report["human_review_status"] != "Reviewed by analyst":
            if st.button("Mark report as reviewed"):
                report["human_review_status"] = "Reviewed by analyst"
                history[selected_report_index] = report
                st.session_state.investigation_history = history
                st.session_state.investigation_report = report
                st.rerun()

elif page == "Data Explorer":
    render_page_heading(
        "Data Explorer",
        "Search, inspect, and export the local synthetic dataset without changing its records.",
    )
    st.caption("Synthetic sample data · Export is limited to the currently filtered view.")
    query = st.text_input("Filter text", placeholder="Try: account, payment, investment...")
    filtered = filter_by_text(analyzed, query)
    min_score = st.slider("Minimum indicator score", 0, 100, 0, 5)
    filtered = filtered[filtered.risk_score >= min_score]
    st.write(f"{len(filtered)} records")
    st.dataframe(
        filtered[
            [
                "timestamp",
                "platform",
                "post_id",
                "text",
                "engagement",
                "risk_score",
                "risk_labels",
                "evidence",
                "validation_issues",
            ]
        ],
        hide_index=True,
    )
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered CSV", csv, "signalsentry_review.csv", "text/csv")

else:
    render_page_heading(
        "About & Safety",
        "Scope, safeguards, and limitations of this local analyst-support demonstration.",
    )
    st.markdown(
        """
**Purpose:** Demonstrate an analyst-support workflow for triaging synthetic records.

**Current prototype capabilities**
- Loads synthetic sample records and reports data-quality warnings.
- Applies transparent, local keyword-based triage rules.
- Shows matched terms and generates an investigation brief from existing Python functions.
- Visualizes only record-to-platform and record-to-rule-label field associations.
- Exports filtered records for review.

**Important limitations**
- No AI model, Meta model, external API, or live feed is running in this phase.
- The indicator score is heuristic and is not a calibrated probability.
- Keyword matches can produce false positives and false negatives.
- The demo does not identify, profile, or accuse real people.
- Human review and independent corroboration are required before consequential action.
"""
    )
    st.subheader("Integration status")
    st.write(api_message)
    if configured:
        st.caption("Credentials may be configured locally, but this phase does not make API requests.")
