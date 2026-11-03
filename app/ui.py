from __future__ import annotations

from html import escape
from typing import Callable, Final

import plotly.graph_objects as go
import streamlit as st


_COMMAND_SHORTCUT = st.components.v2.component(
    "signalsentry_command_shortcut",
    html="<span aria-hidden='true'></span>",
    js="""\
export default function (component) {
  const { parentElement, setTriggerValue } = component
  const doc = parentElement.ownerDocument
  const reducedMotion = doc.defaultView.matchMedia("(prefers-reduced-motion: reduce)").matches
  const animateMetrics = () => {
    if (reducedMotion) return
    for (const metric of doc.querySelectorAll('[data-testid="stMetricValue"]')) {
      const rawValue = metric.textContent.trim().replace(/,/g, "")
      if (!/^-?\\d+(?:\\.\\d+)?$/.test(rawValue) || metric.dataset.ssCounterAnimated) continue
      const target = Number(rawValue)
      metric.dataset.ssCounterAnimated = "true"
      if (!Number.isFinite(target) || target === 0) continue

      const decimals = (rawValue.split(".")[1] || "").length
      const formatter = new Intl.NumberFormat(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })
      const started = performance.now()
      metric.textContent = formatter.format(0)
      const tick = now => {
        const progress = Math.min((now - started) / 560, 1)
        const eased = 1 - Math.pow(1 - progress, 3)
        metric.textContent = formatter.format(target * eased)
        if (progress < 1) requestAnimationFrame(tick)
      }
      requestAnimationFrame(tick)
    }
  }
  const observer = new MutationObserver(animateMetrics)
  observer.observe(doc.body, { childList: true, subtree: true })
  animateMetrics()
  const handler = event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault()
      setTriggerValue("open_palette", true)
    }
  }
  doc.addEventListener("keydown", handler)
  return () => {
    observer.disconnect()
    doc.removeEventListener("keydown", handler)
  }
}
""",
)

_STYLE: Final[str] = """
<style>
    :root {
        --ss-bg: #080b16;
        --ss-surface: #0e1424;
        --ss-surface-raised: #141c30;
        --ss-line: #28334d;
        --ss-text: #edf2ff;
        --ss-muted: #a6b1c8;
        --ss-blue: #77a9ff;
        --ss-cyan: #62e0d1;
        --ss-violet: #a78bfa;
        --ss-magenta: #e879c7;
        --ss-red: #ff737f;
        --ss-amber: #f3bd68;
        --ss-green: #63d6a5;
    }
    .stApp {
        color: var(--ss-text);
        background:
            radial-gradient(ellipse at 75% -18%, rgba(86, 89, 190, .18), transparent 38rem),
            radial-gradient(ellipse at 0% 40%, rgba(34, 128, 178, .08), transparent 34rem),
            var(--ss-bg);
        font-family: Inter, "Segoe UI", Arial, sans-serif;
    }
    .stApp, [data-testid="stSidebar"] { color: var(--ss-text); }
    .stMainBlockContainer { max-width: 1540px; padding-top: 1.2rem; }
    [data-testid="stSidebar"] {
        background: rgba(10, 15, 29, .96);
        border-right: 1px solid rgba(118, 144, 195, .16);
    }
    section[data-testid="stSidebar"] {
        width: 17rem !important;
        min-width: 17rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        border: 1px solid transparent;
        border-radius: 9px;
        padding: .38rem .5rem;
        transition: background .18s ease, border-color .18s ease, transform .18s ease;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(98, 134, 212, .10);
        border-color: rgba(119, 169, 255, .18);
        transform: translateX(2px);
    }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(20, 29, 49, .96), rgba(13, 19, 34, .94));
        border: 1px solid rgba(132, 153, 202, .18);
        border-radius: 14px;
        padding: 15px 17px;
        box-shadow: 0 10px 24px rgba(0, 0, 0, .12);
        transition: border-color .2s ease, transform .2s ease, box-shadow .2s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(119, 169, 255, .42);
        box-shadow: 0 12px 30px rgba(31, 70, 135, .16);
        transform: translateY(-2px);
    }
    div[data-testid="stMetricValue"] { color: #b7d5ff; font-weight: 650; }
    div[data-testid="stMetricLabel"] p {
        color: var(--ss-muted);
        font-size: .79rem;
        font-weight: 550;
    }
    h1, h2, h3 { letter-spacing: -.025em; }
    h2 { font-size: 1.16rem; }
    h3 { font-size: 1rem; }
    [data-testid="stCaptionContainer"] { color: var(--ss-muted); }
    [data-testid="stContainer"] {
        border-color: rgba(132, 153, 202, .17) !important;
    }
    [data-testid="stPlotlyChart"] {
        border-radius: 12px;
        animation: ss-rise .45s ease both;
    }
    [data-testid="stDataFrame"] { border-radius: 12px; }
    [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {
        background: rgba(13, 19, 34, .92);
        border-color: rgba(132, 153, 202, .28);
        border-radius: 10px;
    }
    [data-testid="stButton"] button {
        border-radius: 9px;
        font-weight: 600;
        transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }
    [data-testid="stButton"] button:hover {
        border-color: rgba(119, 169, 255, .62);
        box-shadow: 0 6px 20px rgba(65, 110, 203, .18);
        transform: translateY(-1px);
    }
    :focus-visible { outline: 2px solid var(--ss-cyan) !important; outline-offset: 2px; }

    .ss-topbar {
        display: flex; justify-content: space-between; align-items: center; gap: 1rem;
        border: 1px solid rgba(132, 153, 202, .18); border-radius: 14px;
        padding: 11px 15px; margin-bottom: 1.5rem;
        background: rgba(14, 20, 36, .82); backdrop-filter: blur(12px);
    }
    .ss-brand { font-size: .98rem; letter-spacing: .045em; font-weight: 750; color: var(--ss-text); }
    .ss-brand-mark { color: var(--ss-cyan); }
    .ss-tagline { color: var(--ss-muted); font-size: .75rem; margin-top: 2px; }
    .ss-topbar-right { display: flex; align-items: center; gap: .55rem; flex-wrap: wrap; justify-content: flex-end; }
    .ss-env {
        color: #c5d9ff; background: rgba(80, 120, 206, .15);
        border: 1px solid rgba(119, 169, 255, .35); border-radius: 999px;
        padding: 5px 9px; font-size: .66rem; font-weight: 750; letter-spacing: .08em;
    }
    .ss-status { color: #b9c6d9; font-size: .73rem; }
    .ss-status-dot {
        display: inline-block; width: 7px; height: 7px; border-radius: 50%;
        background: var(--ss-green); margin-right: 6px;
        box-shadow: 0 0 10px rgba(99, 214, 165, .45);
    }
    .ss-hero {
        position: relative; overflow: hidden; min-height: 220px;
        display: flex; align-items: center; justify-content: space-between; gap: 1.5rem;
        padding: clamp(22px, 4vw, 42px); margin-bottom: 1.1rem;
        border-radius: 18px; border: 1px solid rgba(132, 153, 202, .2);
        background:
            radial-gradient(ellipse at 82% 55%, rgba(105, 78, 201, .20), transparent 30%),
            radial-gradient(ellipse at 62% 110%, rgba(41, 154, 182, .14), transparent 36%),
            linear-gradient(120deg, #121a2d, #0d1424 64%, #13152c);
        animation: ss-rise .48s ease both;
    }
    .ss-hero-copy { position: relative; z-index: 1; max-width: 700px; }
    .ss-eyebrow, .ss-kicker {
        color: var(--ss-cyan); text-transform: uppercase; letter-spacing: .13em;
        font-size: .68rem; font-weight: 750;
    }
    .ss-hero h1 {
        margin: .55rem 0 .45rem; color: #f4f6ff;
        font-size: clamp(2rem, 4.1vw, 3.35rem); line-height: 1.04;
        letter-spacing: -.05em; font-weight: 720;
    }
    .ss-hero h1 span { color: #9dc5ff; }
    .ss-hero-copy p { color: #bdc9dc; max-width: 570px; line-height: 1.65; margin: .5rem 0 0; }
    .ss-orb-wrap { flex: 0 0 190px; width: 190px; height: 170px; position: relative; display: grid; place-items: center; }
    .ss-orb {
        width: 112px; height: 112px; border-radius: 50%;
        border: 1px solid rgba(132, 191, 255, .72);
        background: radial-gradient(circle at 35% 30%, rgba(109, 221, 231, .7), rgba(96, 123, 236, .22) 30%, rgba(32, 42, 84, .45) 68%, rgba(14, 20, 36, .2));
        box-shadow: inset 0 0 28px rgba(111, 187, 255, .26), 0 0 52px rgba(89, 129, 244, .18);
        animation: ss-orbit 8s linear infinite;
    }
    .ss-orb::before, .ss-orb::after {
        content: ""; position: absolute; inset: -15px -27px; border: 1px solid rgba(103, 207, 220, .3);
        border-radius: 50%; transform: rotate(-28deg);
    }
    .ss-orb::after { inset: -27px -11px; border-color: rgba(159, 130, 245, .3); transform: rotate(48deg); }
    .ss-page-title {
        color: #f0f3ff; font-size: clamp(1.65rem, 2.8vw, 2.25rem);
        font-weight: 700; letter-spacing: -.035em; margin: .18rem 0 .25rem;
    }
    .ss-page-description { color: var(--ss-muted); margin-bottom: 1.15rem; font-size: .9rem; }
    .ss-panel-title { color: #e7edff; font-weight: 650; font-size: .95rem; }
    .ss-alert {
        border: 1px solid rgba(132, 153, 202, .17); border-left: 3px solid var(--ss-blue);
        border-radius: 11px; background: linear-gradient(115deg, rgba(18, 27, 46, .96), rgba(13, 19, 33, .96));
        padding: 12px 14px; margin: .3rem 0 .6rem;
        transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
        animation: ss-rise .38s ease both;
    }
    .ss-alert:hover { transform: translateY(-2px); border-color: rgba(119, 169, 255, .42); box-shadow: 0 9px 22px rgba(0, 0, 0, .18); }
    .ss-alert-critical { border-left-color: var(--ss-red); }
    .ss-alert-warning { border-left-color: var(--ss-amber); }
    .ss-alert-info { border-left-color: var(--ss-blue); }
    .ss-alert-head { display:flex; align-items:center; justify-content:space-between; gap:.6rem; }
    .ss-alert-id { color:#f1f4ff; font-size:.9rem; font-weight:700; }
    .ss-severity { font-size:.64rem; font-weight:750; letter-spacing:.08em; }
    .ss-severity-critical { color:#ff9da5; }
    .ss-severity-warning { color:#f4cd86; }
    .ss-severity-info { color:#9dc6ff; }
    .ss-alert-meta { color:var(--ss-muted); font-size:.75rem; line-height:1.55; margin-top:.32rem; }
    .ss-alert-preview { color:#d5deef; font-size:.78rem; line-height:1.5; margin-top:.38rem; }
    .ss-empty {
        padding: 16px 18px; border: 1px dashed rgba(132, 153, 202, .25);
        border-radius: 12px; background: rgba(14, 20, 36, .55);
    }
    .ss-empty-title { color:#dce5f6; font-weight:650; }
    .ss-empty-copy { color:var(--ss-muted); font-size:.82rem; margin-top:.2rem; }
    .ss-timeline { border-left: 1px solid rgba(98, 224, 209, .35); padding-left: 13px; margin-left: 4px; }
    .ss-timeline-step { position:relative; padding: 0 0 12px; color:#d7e0f0; font-size:.84rem; }
    .ss-timeline-step::before {
        content:""; position:absolute; width:7px; height:7px; border-radius:50%;
        background:var(--ss-cyan); left:-17px; top:5px; box-shadow:0 0 10px rgba(98,224,209,.35);
    }
    .ss-footnote { color:#9baac0; font-size:.76rem; }
    @keyframes ss-rise { from { opacity:0; transform:translateY(7px); } to { opacity:1; transform:translateY(0); } }
    @keyframes ss-orbit { to { transform:rotate(360deg); } }
    @media (max-width: 720px) {
        .ss-topbar { align-items:flex-start; flex-direction:column; }
        .ss-topbar-right { justify-content:flex-start; }
        .ss-hero { min-height:190px; flex-direction:column; align-items:flex-start; }
        .ss-hero-copy { width:100%; max-width:100%; }
        .ss-hero-copy p { max-width:100%; }
        .ss-orb-wrap { position:absolute; right:10px; bottom:8px; z-index:0; width:82px; height:82px; opacity:.32; }
        .ss-orb { width:76px; height:76px; }
        .st-key-command-center-hero [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; }
        .st-key-command-center-hero [data-testid="stHorizontalBlock"] > div {
            flex:1 1 100% !important; width:100% !important; min-width:100% !important;
        }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; scroll-behavior:auto !important; transition-duration:.01ms !important; }
    }
</style>
"""

PAGES: Final[tuple[str, ...]] = (
    "Command center",
    "Investigation workspace",
    "Threat intelligence",
    "Network intelligence",
    "Investigation report",
    "Data Explorer",
    "About & Safety",
)


def apply_design_system() -> None:
    st.markdown(_STYLE, unsafe_allow_html=True)


def render_topbar() -> None:
    st.markdown(
        """
<div class="ss-topbar">
  <div>
    <div class="ss-brand">SIGNALSENTRY <span class="ss-brand-mark">✳</span> AI</div>
    <div class="ss-tagline">From suspicious signals to explainable intelligence.</div>
  </div>
  <div class="ss-topbar-right">
    <span class="ss-env">LOCAL / SYNTHETIC</span>
    <span class="ss-status"><span class="ss-status-dot"></span>Local rules active</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
<section class="ss-hero">
  <div class="ss-hero-copy">
    <div class="ss-eyebrow">SignalSentry intelligence workspace</div>
    <h1>From suspicious signals<br>to <span>explainable intelligence.</span></h1>
    <p>Investigate synthetic indicators with transparent evidence, clear uncertainty, and the analyst in control.</p>
  </div>
  <div class="ss-orb-wrap" aria-label="Abstract signal visualization">
    <div class="ss-orb"></div>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )


def render_page_heading(title: str, description: str) -> None:
    st.markdown(
        f'<div class="ss-kicker">Analyst workspace</div>'
        f'<h1 class="ss-page-title">{escape(title)}</h1>'
        f'<div class="ss-page-description">{escape(description)}</div>',
        unsafe_allow_html=True,
    )


def style_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c5cee2", family='Inter, "Segoe UI", sans-serif', size=11),
        margin=dict(l=12, r=12, t=30, b=14),
        colorway=["#77a9ff", "#62e0d1", "#a78bfa", "#f3bd68", "#e879c7"],
        xaxis=dict(gridcolor="rgba(136, 154, 195, .12)", zerolinecolor="rgba(136, 154, 195, .18)"),
        yaxis=dict(gridcolor="rgba(136, 154, 195, .12)", zerolinecolor="rgba(136, 154, 195, .18)"),
        hoverlabel=dict(bgcolor="#161e31", bordercolor="#526184", font_color="#edf2ff"),
    )
    return fig


def render_alert_card(
    record_id: object,
    platform: object,
    score: int,
    labels: list[str],
    evidence: list[str],
    preview: str,
) -> None:
    severity, level = severity_for_score(score)
    label_text = ", ".join(escape(str(label)) for label in labels) or "No matched rule"
    evidence_text = ", ".join(escape(str(term)) for term in evidence) or "No evidence terms matched"
    preview_text = escape(preview.strip())
    if len(preview_text) > 140:
        preview_text = f"{preview_text[:137]}..."
    st.markdown(
        f'<article class="ss-alert ss-alert-{level}">'
        f'<div class="ss-alert-head"><span class="ss-alert-id">{escape(str(record_id))}</span>'
        f'<span class="ss-severity ss-severity-{level}">{severity} · {score}/100</span></div>'
        f'<div class="ss-alert-meta">{escape(str(platform))} · {label_text}</div>'
        f'<div class="ss-alert-meta">Evidence: {evidence_text}</div>'
        f'<div class="ss-alert-preview">{preview_text}</div>'
        f'</article>',
        unsafe_allow_html=True,
    )


def severity_for_score(score: int) -> tuple[str, str]:
    if score >= 60:
        return "HIGH INDICATOR", "critical"
    if score >= 30:
        return "REVIEW", "warning"
    return "INFORMATIONAL", "info"


def render_empty_state(title: str, description: str) -> None:
    st.markdown(
        f'<div class="ss-empty"><div class="ss-empty-title">{escape(title)}</div>'
        f'<div class="ss-empty-copy">{escape(description)}</div></div>',
        unsafe_allow_html=True,
    )


def command_shortcut(*, key: str, on_open: Callable[[], None]) -> None:
    _COMMAND_SHORTCUT(
        key=key,
        data={},
        on_open_palette_change=on_open,
        width="content",
        height=1,
    )
