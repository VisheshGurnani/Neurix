import os
import re
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st


# -----------------------------------------------------------------------------
# Page configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Neurix — Repository Intelligence",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

API_URL = "https://neurix-g2k3.onrender.com"
DEFAULT_REPO = "https://github.com/VisheshGurnani/Neurix"

STAGES = [
    ("Ingesting repository", "Connecting to GitHub remote & shallow-cloning HEAD"),
    ("Filtering & mapping", "Pruning binary artifacts, cache trees, and irrelevant directories"),
    ("Scoring priority files", "Ranking manifests, entry points, and high-value source files"),
    ("Bounding context window", "Structuring readable text within the analysis limit"),
    ("Synthesizing technical brief", "Generating the repository explanation"),
]


# -----------------------------------------------------------------------------
# Styling — ported from the AI Studio visual direction
# -----------------------------------------------------------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #080b11;
    --surface: #0e131f;
    --surface-2: #0b0f17;
    --surface-3: #090d15;
    --border: rgba(255,255,255,.075);
    --border-strong: rgba(255,255,255,.12);
    --text: #ededed;
    --secondary: #8e9bb0;
    --muted: #536077;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --green: #34d399;
    --danger: #f87171;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 50% -10%, rgba(59,130,246,.07), transparent 34%),
        var(--bg) !important;
}

[data-testid="stHeader"] {
    background: rgba(8,11,17,.90) !important;
    border-bottom: 1px solid var(--border) !important;
}

.block-container {
    max-width: 1480px !important;
    padding: 0 3rem 3rem !important;
}

section[data-testid="stSidebar"] {
    background: #080b11 !important;
}

h1, h2, h3, h4 {
    font-family: "Space Grotesk", Inter, sans-serif !important;
    letter-spacing: -.035em !important;
}

p, label, .stMarkdown, .stTextInput, .stButton {
    font-family: Inter, sans-serif !important;
}

code, pre, .mono {
    font-family: "JetBrains Mono", monospace !important;
}

/* Top navigation */
.neurix-nav {
    height: 68px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-mark {
    width: 30px;
    height: 30px;
    border-radius: 7px;
    border: 1px solid rgba(59,130,246,.38);
    background: #0e1628;
    color: #60a5fa;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Space Grotesk", sans-serif;
    font-weight: 700;
}

.brand-name {
    color: white;
    font-family: "Space Grotesk", sans-serif;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: .12em;
}

.brand-sub {
    color: var(--muted);
    font: 10px "JetBrains Mono", monospace;
    border-left: 1px solid var(--border);
    padding-left: 12px;
    letter-spacing: .04em;
}

.status-dot {
    width: 7px;
    height: 7px;
    display: inline-block;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 10px rgba(52,211,153,.4);
}

/* Hero */
.hero {
    padding: 82px 0 42px;
}

.eyebrow {
    color: #60a5fa;
    font: 600 10px "JetBrains Mono", monospace;
    letter-spacing: .16em;
    text-transform: uppercase;
    margin-bottom: 18px;
}

.hero h1 {
    color: white;
    font-size: clamp(42px, 5.2vw, 72px);
    line-height: 1.02;
    margin: 0;
    max-width: 920px;
}

.hero h1 span {
    color: #64748b;
}

.hero-copy {
    color: var(--secondary);
    font-size: 16px;
    line-height: 1.75;
    max-width: 760px;
    margin-top: 22px;
}

/* Input shell */
.command-shell {
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: 14px;
    padding: 10px;
    box-shadow: 0 18px 60px rgba(0,0,0,.28);
}

.command-meta {
    color: var(--muted);
    font: 10px "JetBrains Mono", monospace;
    text-transform: uppercase;
    letter-spacing: .08em;
}

.supporting {
    color: var(--muted);
    font: 10px "JetBrains Mono", monospace;
    letter-spacing: .03em;
    margin-top: 12px;
}

/* Streamlit inputs */
div[data-testid="stTextInput"] input {
    background: #090d15 !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,.08) !important;
    border-radius: 9px !important;
    font-family: "JetBrains Mono", monospace !important;
    font-size: 13px !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: rgba(59,130,246,.6) !important;
    box-shadow: 0 0 0 1px rgba(59,130,246,.22) !important;
}

div[data-testid="stButton"] > button {
    background: #2563eb !important;
    color: white !important;
    border: 1px solid rgba(96,165,250,.35) !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    min-height: 42px !important;
}

div[data-testid="stButton"] > button:hover {
    background: #3b82f6 !important;
    border-color: rgba(96,165,250,.65) !important;
}

div[data-testid="stSlider"] {
    padding-top: 4px;
}

/* Panels */
.panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 13px;
    padding: 24px;
}

.panel-dark {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 13px;
    padding: 24px;
}

.section-label {
    color: white;
    font: 600 15px "Space Grotesk", sans-serif;
}

.section-sub {
    color: var(--secondary);
    font-size: 12px;
    margin-top: 4px;
}

.metric {
    background: var(--surface-3);
    border: 1px solid var(--border);
    border-radius: 11px;
    padding: 17px;
}

.metric-label {
    color: var(--muted);
    font: 10px "JetBrains Mono", monospace;
    text-transform: uppercase;
    letter-spacing: .08em;
}

.metric-value {
    color: white;
    font: 600 20px "Space Grotesk", sans-serif;
    margin-top: 6px;
}

.tech-pill {
    display: inline-block;
    padding: 7px 10px;
    margin: 3px;
    border-radius: 7px;
    background: rgba(59,130,246,.08);
    border: 1px solid rgba(59,130,246,.18);
    color: #93c5fd;
    font: 11px "JetBrains Mono", monospace;
}

.pipeline {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0;
    margin-top: 22px;
}

.pipeline-step {
    padding: 17px;
    border-top: 1px solid var(--border-strong);
    border-right: 1px solid var(--border);
    background: rgba(14,19,31,.65);
}

.pipeline-step:last-child {
    border-right: 0;
}

.pipeline-num {
    color: #60a5fa;
    font: 600 11px "JetBrains Mono", monospace;
}

.pipeline-title {
    color: white;
    font-size: 12px;
    font-weight: 600;
    margin-top: 8px;
}

.pipeline-detail {
    color: var(--muted);
    font-size: 10px;
    line-height: 1.55;
    margin-top: 6px;
}

.file-row {
    background: #090d15;
    border: 1px solid rgba(255,255,255,.055);
    border-radius: 8px;
    padding: 10px 12px;
    margin: 5px 0;
}

.file-path {
    color: #c5cede;
    font: 11px "JetBrains Mono", monospace;
}

.file-meta {
    color: var(--muted);
    font: 10px "JetBrains Mono", monospace;
}

.arch-node {
    background: #090d15;
    border: 1px solid rgba(59,130,246,.2);
    border-radius: 10px;
    padding: 13px 15px;
    color: #dbeafe;
    font: 11px "JetBrains Mono", monospace;
    text-align: center;
}

.arch-arrow {
    color: #3b82f6;
    text-align: center;
    font: 14px "JetBrains Mono", monospace;
    padding: 5px;
}

.footer {
    border-top: 1px solid var(--border);
    margin-top: 70px;
    padding: 24px 0;
    color: var(--muted);
    font: 10px "JetBrains Mono", monospace;
}

div[data-testid="stAlert"] {
    background: rgba(248,113,113,.08) !important;
    border: 1px solid rgba(248,113,113,.18) !important;
}

@media (max-width: 900px) {
    .block-container {
        padding: 0 1rem 2rem !important;
    }
    .hero {
        padding-top: 50px;
    }
    .pipeline {
        grid-template-columns: 1fr;
    }
    .pipeline-step {
        border-right: 0;
        border-bottom: 1px solid var(--border);
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def api_get(path: str, timeout: float = 8.0) -> Optional[Dict[str, Any]]:
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{API_URL}{path}")
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


def api_post(path: str, payload: Dict[str, Any], timeout: float = 180.0) -> Dict[str, Any]:
    with httpx.Client(timeout=timeout) as client:
        response = client.post(f"{API_URL}{path}", json=payload)
        response.raise_for_status()
        return response.json()


def render_markdown(text: str) -> None:
    """Render the model's Markdown using Streamlit's native Markdown renderer."""
    st.markdown(text)


def repo_label(repo: str) -> str:
    return repo.split("/")[-1] if "/" in repo else repo


def reset_analysis() -> None:
    st.session_state.result = None
    st.session_state.error = None
    st.session_state.active_tab = "Overview"


# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------

defaults = {
    "result": None,
    "error": None,
    "active_tab": "Overview",
    "github_url": "",
    "max_files": 12,
    "backend_status": None,
    "backend_model": "Unknown",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------------------------------------------------------
# Backend status
# -----------------------------------------------------------------------------

if st.session_state.backend_status is None:
    health = api_get("/health")
    st.session_state.backend_status = bool(health and health.get("status") == "healthy")

config = api_get("/config")
if config:
    st.session_state.backend_model = config.get("groq_model", "Unknown")


# -----------------------------------------------------------------------------
# Navigation
# -----------------------------------------------------------------------------

st.markdown(
    """
<div class="neurix-nav">
    <div class="brand">
        <div class="brand-mark">N</div>
        <div class="brand-name">NEURIX</div>
        <div class="brand-sub">REPOSITORY INTELLIGENCE</div>
    </div>
    <div style="display:flex;align-items:center;gap:18px;color:#536077;font:10px 'JetBrains Mono',monospace;">
        <span>READ-ONLY ANALYSIS</span>
        <span>·</span>
        <span><span class="status-dot"></span> SYSTEM OPERATIONAL</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Results mode
# -----------------------------------------------------------------------------

result = st.session_state.result

if result:
    repo = result.get("repository", "Unknown repository")
    model = result.get("model_used") or st.session_state.backend_model
    files_analyzed = result.get("files_analyzed", 0)
    tech_stack = result.get("tech_stack") or []
    detected_files = result.get("detected_files") or []

    st.markdown(
        f"""
<div style="padding:42px 0 20px;">
    <div class="eyebrow">REPOSITORY INTELLIGENCE · ANALYSIS COMPLETE</div>
    <h1 style="font-size:42px;color:white;margin:0;">{repo_label(repo)}</h1>
    <div style="color:#8e9bb0;font:12px 'JetBrains Mono',monospace;margin-top:8px;">{repo}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("FILES ANALYZED", str(files_analyzed)),
        ("MODEL", model),
        ("CONTEXT", "TRUNCATED" if result.get("context_truncated") else "WITHIN LIMIT"),
        ("BACKEND", "FASTAPI"),
    ]
    for col, (label, value) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(
                f'<div class="metric"><div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    tabs = ["Overview", "Architecture", "Tech Stack", "Files", "Raw"]
    selected = st.tabs(tabs)

    # -------------------------------------------------------------------------
    # Overview
    # -------------------------------------------------------------------------
    with selected[0]:
        st.markdown(
            """
<div class="panel">
    <div class="section-label">Technical Brief</div>
    <div class="section-sub">Generated from prioritized repository files.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("")
        render_markdown(result.get("explanation") or "No explanation returned.")

    # -------------------------------------------------------------------------
    # Architecture
    # -------------------------------------------------------------------------
    with selected[1]:
        st.markdown(
            """
<div class="panel">
    <div class="section-label">Repository Architecture</div>
    <div class="section-sub">A simplified view of how Neurix understands the analyzed codebase.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        cols = st.columns([1, 0.25, 1, 0.25, 1, 0.25, 1])
        nodes = [
            ("GitHub Repository", "Source"),
            ("Repository Processor", "Filtering"),
            ("Priority Files", "Context"),
            ("AI Explanation", "Synthesis"),
        ]

        for i, (title, subtitle) in enumerate(nodes):
            with cols[i * 2]:
                st.markdown(
                    f'<div class="arch-node"><strong>{title}</strong><br>'
                    f'<span style="color:#536077">{subtitle}</span></div>',
                    unsafe_allow_html=True,
                )
            if i < len(nodes) - 1:
                with cols[i * 2 + 1]:
                    st.markdown('<div class="arch-arrow">→</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

        st.markdown(
            """
<div class="panel-dark">
    <div class="section-label">How the analysis works</div>
    <div class="pipeline">
        <div class="pipeline-step"><div class="pipeline-num">01</div><div class="pipeline-title">Ingest</div><div class="pipeline-detail">Shallow-clone the public repository.</div></div>
        <div class="pipeline-step"><div class="pipeline-num">02</div><div class="pipeline-title">Filter</div><div class="pipeline-detail">Ignore binaries, caches and generated trees.</div></div>
        <div class="pipeline-step"><div class="pipeline-num">03</div><div class="pipeline-title">Rank</div><div class="pipeline-detail">Prioritize manifests, docs and entry points.</div></div>
        <div class="pipeline-step"><div class="pipeline-num">04</div><div class="pipeline-title">Bound</div><div class="pipeline-detail">Keep the model context within limits.</div></div>
        <div class="pipeline-step"><div class="pipeline-num">05</div><div class="pipeline-title">Explain</div><div class="pipeline-detail">Generate a human-readable technical brief.</div></div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # Tech stack
    # -------------------------------------------------------------------------
    with selected[2]:
        st.markdown(
            """
<div class="panel">
    <div class="section-label">Detected Technology Ecosystem</div>
    <div class="section-sub">Inferred from repository manifests, imports and source files.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

        if tech_stack:
            html = "".join(f'<span class="tech-pill">{t}</span>' for t in tech_stack)
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("No specific technology indicators were returned by the backend.")

    # -------------------------------------------------------------------------
    # Files
    # -------------------------------------------------------------------------
    with selected[3]:
        st.markdown(
            """
<div class="panel">
    <div class="section-label">Analyzed File Hierarchy</div>
    <div class="section-sub">Prioritized files selected by the repository processor.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        if not detected_files:
            st.info(
                "The backend returned no file metadata. The analysis itself is still available "
                "under Overview."
            )
        else:
            search = st.text_input(
                "Filter file path",
                placeholder="e.g. backend/main.py",
                label_visibility="collapsed",
            ).lower()

            categories = ["All"] + sorted(
                {str(f.get("category", "Source")) for f in detected_files}
            )
            category = st.selectbox("Category", categories, label_visibility="collapsed")

            visible = []
            for f in detected_files:
                path = str(f.get("path", ""))
                cat = str(f.get("category", "Source"))
                if search and search not in path.lower():
                    continue
                if category != "All" and cat != category:
                    continue
                visible.append(f)

            for f in visible:
                path = str(f.get("path", ""))
                priority = f.get("priority", 0)
                size = int(f.get("size", 0))
                cat = str(f.get("category", "Source"))
                snippet = str(f.get("snippet", ""))

                with st.expander(f"{path}  ·  {size / 1024:.1f} KB  ·  {cat}"):
                    st.caption(f"Priority: {priority}/10")
                    if snippet:
                        st.code(snippet, language="text")

    # -------------------------------------------------------------------------
    # Raw
    # -------------------------------------------------------------------------
    with selected[4]:
        st.markdown(
            """
<div class="panel">
    <div class="section-label">Raw Model Response</div>
    <div class="section-sub">Unmodified explanation returned by the backend.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.code(result.get("explanation") or "", language="markdown")

    st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)

    if st.button("↻  Analyze another repository", use_container_width=False):
        reset_analysis()
        st.rerun()

else:
    # -------------------------------------------------------------------------
    # Landing page
    # -------------------------------------------------------------------------
    st.markdown(
        """
<div class="hero">
    <div class="eyebrow">CODEBASE ARCHITECTURE ENGINE</div>
    <h1>Understand any codebase.<br><span>Without reading 10,000 lines.</span></h1>
    <div class="hero-copy">
        Neurix shallow-clones public GitHub repositories, ranks architectural
        manifests, isolates entry points, and produces an authoritative technical
        brief in seconds.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Command interface
    st.markdown('<div class="command-shell">', unsafe_allow_html=True)

    st.markdown(
        '<div class="command-meta">GitHub repository target</div>',
        unsafe_allow_html=True,
    )

    st.session_state.github_url = st.text_input(
        "GitHub repository URL",
        value=st.session_state.github_url,
        placeholder="https://github.com/owner/repository",
        label_visibility="collapsed",
        key="repo_input",
    )

    col_a, col_b = st.columns([4, 1])

    with col_a:
        st.session_state.max_files = st.slider(
            "Analysis depth",
            min_value=5,
            max_value=30,
            value=st.session_state.max_files,
            help="Maximum number of prioritized repository files sent to the backend.",
        )

    with col_b:
        st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
        analyze = st.button("Analyze  →", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="supporting">READ-ONLY ANALYSIS · NO CODE EXECUTION · EPHEMERAL SHALLOW CLONE</div>',
        unsafe_allow_html=True,
    )

    # Status
    status_text = "SYSTEM OPERATIONAL" if st.session_state.backend_status else "BACKEND UNAVAILABLE"
    status_color = "#34d399" if st.session_state.backend_status else "#f87171"

    st.markdown(
        f'<div style="margin-top:18px;color:#536077;font:10px JetBrains Mono,monospace;">'
        f'<span style="color:{status_color}">●</span> {status_text} '
        f'&nbsp; · &nbsp; MODEL {st.session_state.backend_model}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Presets
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
<div class="section-label">Curated targets</div>
<div class="section-sub">Use one of these to verify the pipeline end-to-end.</div>
""",
        unsafe_allow_html=True,
    )

    p1, p2, p3 = st.columns(3)

    presets = [
        ("Neurix", DEFAULT_REPO),
        ("Flask", "https://github.com/pallets/flask"),
        ("Express", "https://github.com/expressjs/express"),
    ]

    for col, (name, url) in zip([p1, p2, p3], presets):
        with col:
            if st.button(name, use_container_width=True):
                st.session_state.github_url = url
                st.rerun()

    # How it works
    st.markdown("<div style='height:42px'></div>", unsafe_allow_html=True)

    st.markdown(
        """
<div class="section-label">How Neurix thinks about a codebase</div>
<div class="section-sub">A small, deterministic pipeline before the model sees anything.</div>
<div class="pipeline">
    <div class="pipeline-step"><div class="pipeline-num">01</div><div class="pipeline-title">Read</div><div class="pipeline-detail">Shallow-clone and inspect relevant text files.</div></div>
    <div class="pipeline-step"><div class="pipeline-num">02</div><div class="pipeline-title">Filter</div><div class="pipeline-detail">Remove binaries, caches and generated directories.</div></div>
    <div class="pipeline-step"><div class="pipeline-num">03</div><div class="pipeline-title">Map</div><div class="pipeline-detail">Prioritize docs, configs and entry points.</div></div>
    <div class="pipeline-step"><div class="pipeline-num">04</div><div class="pipeline-title">Bound</div><div class="pipeline-detail">Keep repository context inside the model limit.</div></div>
    <div class="pipeline-step"><div class="pipeline-num">05</div><div class="pipeline-title">Explain</div><div class="pipeline-detail">Turn structure into language humans can use.</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # Analyze
    # -------------------------------------------------------------------------
    if analyze:
        target = st.session_state.github_url.strip()

        if not target:
            st.session_state.error = "Please provide a public GitHub repository URL."
            st.rerun()

        if not re.match(r"^https://github\.com/[^/]+/[^/]+/?$", target):
            st.session_state.error = (
                "Invalid repository target. Use https://github.com/owner/repository"
            )
            st.rerun()

        st.session_state.error = None

        progress = st.progress(0)
        stage_box = st.empty()

        try:
            for i, (title, detail) in enumerate(STAGES):
                stage_box.markdown(
                    f"""
<div class="panel-dark">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
            <div class="section-label">{title}</div>
            <div class="section-sub">{detail}</div>
        </div>
        <div style="color:#60a5fa;font:11px JetBrains Mono,monospace;">STAGE {i+1}/5</div>
    </div>
</div>
""",
                    unsafe_allow_html=True,
                )
                # The actual backend call happens at the final stage.
                progress.progress((i + 1) / len(STAGES))

                if i == len(STAGES) - 1:
                    data = api_post(
                        "/explain",
                        {
                            "url": target,
                            "max_files": st.session_state.max_files,
                        },
                        timeout=240.0,
                    )

            progress.empty()
            stage_box.empty()

            if data.get("success"):
                st.session_state.result = data
                st.session_state.github_url = target
                st.rerun()
            else:
                st.session_state.error = (
                    data.get("error")
                    or data.get("message")
                    or "Analysis could not be completed."
                )
                st.rerun()

        except Exception as exc:
            progress.empty()
            stage_box.empty()
            st.session_state.error = (
                f"Could not reach the Neurix backend at {API_URL}. "
                f"Details: {exc}"
            )
            st.rerun()

    if st.session_state.error:
        st.error(st.session_state.error)


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.markdown(
    """
<div class="footer">
    <div style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;">
        <span><strong style="color:white;">NEURIX</strong> — Understand any codebase before you touch it.</span>
        <span>READ-ONLY · FASTAPI · GROQ · GITPYTHON</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)
