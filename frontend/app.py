import streamlit as st
import requests
import plotly.graph_objects as go

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="INSYTE",
    page_icon="😈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Session State Init ──────────────────────────────────────────────────────
for k, v in [("result", None), ("trending", None), ("conn_err", False),
             ("api_err", ""), ("trend_err", ""), ("history", []),
             ("query", ""), ("lim_val", 80), ("dark_mode", True)]:
    if k not in st.session_state:
        st.session_state[k] = v

IS_DARK = st.session_state["dark_mode"]

# ─── Colour Palettes (Solid SaaS Aesthetic) ──────────────────────────────────
DARK = {
    "bg":         "#0e0f11",
    "surface":    "#14151a",
    "surface2":   "#1a1b22",
    "border":     "#25262e",
    "border2":    "#2e2f3a",
    "text":       "#d4d0c8",
    "text_dim":   "#8b8c9a",
    "text_faint": "#4a4b59",
    "amber":      "#d4a33d",
    "sage":       "#639976",
    "slate":      "#6585ab",
    "rust":       "#b3573f",
    "mauve":      "#876599",
    "steel":      "#537587",
    "olive":      "#87993f",
    "rose":       "#996574",
    "plot_bg":    "rgba(0,0,0,0)",
    "grid":       "#25262e",
}
LIGHT = {
    "bg":         "#f7f6f2",
    "surface":    "#ffffff",
    "surface2":   "#f0efe9",
    "border":     "#dcdad2",
    "border2":    "#c9c7be",
    "text":       "#1a1917",
    "text_dim":   "#5c5a52",
    "text_faint": "#9e9c93",
    "amber":      "#b8820b",
    "sage":       "#3d704e",
    "slate":      "#40628a",
    "rust":       "#8a331c",
    "mauve":      "#624075",
    "steel":      "#2e4f61",
    "olive":      "#62751c",
    "rose":       "#75404e",
    "plot_bg":    "rgba(255,255,255,0)",
    "grid":       "#dcdad2",
}
C = DARK if IS_DARK else LIGHT

# ─── Dynamic Slider Color ───────────────────────────────────────────────────
def slider_color(v):
    if v >= 70:
        return C["sage"]
    elif v >= 45:
        return C["amber"]
    return C["rust"]

SLIDER_COLOR = slider_color(st.session_state.lim_val)

EMOTION_COLORS = {
    "joy":      C["amber"], "love":     C["rose"],
    "surprise": C["slate"], "fear":     C["mauve"],
    "anger":    C["rust"],  "sadness":  C["steel"],
    "disgust":  C["olive"], "neutral":  C["text_dim"],
}
PILL_COLORS = [C["amber"], C["sage"], C["slate"], C["rust"], C["mauve"]]
RANK_COLORS = [C["amber"], C["sage"], C["slate"], C["rust"],
               C["mauve"], C["steel"], C["olive"], C["rose"]]

API_BASE = "http://localhost:8000"

# ─── CSS ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600&display=swap');

html, body, .stApp {{
    background: {C["bg"]} !important;
    color: {C["text"]};
    font-family: 'DM Sans', sans-serif;
    font-size: 18px; /* Increased base font size */
}}
.main .block-container {{
    padding: 2rem 4rem 6rem 4rem; /* Increased padding */
    max-width: 1600px;
}}
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {C["bg"]}; }}
::-webkit-scrollbar-thumb {{ background: {C["border2"]}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {C["amber"]}; }}

.sec-lbl {{
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {C["amber"]};
    margin-bottom: 1.5rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid {C["border"]};
}}

/* ── SEARCH BAR FIX ── */
.stTextInput>div>div>input {{
    background: {C["surface"]} !important;
    border: 2px solid {C["border2"]} !important;
    color: {C["text"]} !important;
    padding: 1.25rem 1.75rem !important; /* Fixed text cutoff */
    font-size: 1.25rem !important;
    font-family: 'DM Sans', sans-serif !important;
    border-radius: 8px !important;
    line-height: 1.5 !important;
    height: auto !important; 
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
.stTextInput>div>div>input:focus {{
    border-color: {C["amber"]} !important;
    box-shadow: 0 0 0 3px {C["amber"]}22 !important;
}}
.stTextInput>label {{ display: none !important; }}

/* ── SLIDER FIX (Overriding Streamlit Defaults) ── */
.stSlider>label {{
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.1em !important;
    color: {C["text_dim"]} !important;
    text-transform: uppercase !important;
}}
div[data-testid="stSlider"] div[data-baseweb="slider"] div[data-testid="stSliderTrackFilled"] {{
    background-color: {SLIDER_COLOR} !important;
}}
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] {{
    background-color: {SLIDER_COLOR} !important;
    border-color: {SLIDER_COLOR} !important;
    box-shadow: 0 0 0 4px {SLIDER_COLOR}30 !important;
}}

/* ── BUTTONS ── */
.stButton>button {{
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    background: {C["surface2"]} !important;
    color: {C["text"]} !important;
    border: 1px solid {C["border2"]} !important;
    border-radius: 6px !important;
    padding: 0.8rem 1rem !important;
    transition: all 0.15s ease-in-out !important;
    width: 100% !important;
}}
.stButton>button:hover {{
    background: {C["amber"]}15 !important;
    border-color: {C["amber"]} !important;
    color: {C["amber"]} !important;
}}

/* Run Analysis Primary Button */
.run-btn .stButton>button {{
    background: {C["amber"]} !important;
    color: {C["bg"]} !important;
    border-color: {C["amber"]} !important;
    font-size: 1.1rem !important;
    height: 3.8rem !important;
    margin-top: 0.2rem !important;
}}
.run-btn .stButton>button:hover {{
    background: {C["amber"]}ee !important;
    color: {C["bg"]} !important;
    transform: translateY(-2px);
}}

/* Preset pill buttons */
div[data-testid="column"] .stButton>button {{
    font-size: 0.8rem !important;
    padding: 0.7rem 0.5rem !important;
    border-radius: 6px !important;
    letter-spacing: 0.05em !important;
    white-space: nowrap !important;
}}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
    background: transparent !important;
    border-bottom: 1px solid {C["border"]} !important;
    gap: 1.5rem !important;
    justify-content: center !important; /* Centered tabs */
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {C["text_dim"]} !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 1.2rem 2.5rem !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    margin-bottom: -2px !important;
}}
.stTabs [aria-selected="true"] {{
    color: {C["amber"]} !important;
    border-bottom: 3px solid {C["amber"]} !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 3.5rem !important; }}

/* ── CARDS & PANELS ── */
.m-tile {{
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 10px;
    padding: 2rem 1.8rem;
    position: relative;
    overflow: hidden;
    height: 100%;
}}
.m-tile-bar {{ position: absolute; top: 0; left: 0; right: 0; height: 4px; }}
.m-tile-lbl {{
    font-family: 'Space Mono', monospace; font-size: 0.75rem;
    letter-spacing: 0.16em; text-transform: uppercase;
    color: {C["text_dim"]}; margin-bottom: 1rem;
}}
.m-tile-val {{
    font-family: 'Syne', sans-serif; font-weight: 800;
    font-size: 2.8rem; line-height: 1; margin-bottom: 0.5rem;
}}
.m-tile-sub {{ font-family: 'DM Sans', sans-serif; font-size: 0.9rem; color: {C["text_dim"]}; }}

.panel {{
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 10px;
    padding: 2.2rem;
    height: 100%;
}}
.panel-ttl {{
    font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem;
    letter-spacing: 0.1em; text-transform: uppercase; color: {C["text_dim"]};
    margin-bottom: 1.5rem; padding-bottom: 1rem;
    border-bottom: 1px solid {C["border"]};
}}

.score-block {{
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-top: 5px solid {C["amber"]};
    border-radius: 10px;
    padding: 2.8rem 2.5rem;
    height: 100%;
}}
.score-num {{
    font-family: 'Syne', sans-serif; font-weight: 800;
    font-size: 6.5rem; line-height: 1; letter-spacing: -0.05em;
}}
.score-sub {{
    font-family: 'Space Mono', monospace; font-size: 0.8rem;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: {C["text_dim"]}; margin-top: 0.8rem; margin-bottom: 2rem;
}}
.rec-txt {{
    font-family: 'DM Sans', sans-serif; font-size: 1.15rem;
    font-weight: 500; line-height: 1.65;
    padding-top: 1.8rem; border-top: 1px solid {C["border"]};
}}

.risk-bdg {{
    display: inline-flex; align-items: center; gap: 0.6rem;
    font-family: 'Space Mono', monospace; font-size: 0.8rem;
    letter-spacing: 0.12em; text-transform: uppercase;
    padding: 0.6rem 1.2rem; border-radius: 6px; border: 1px solid;
    background: {C["surface2"]};
}}
.kw-pill {{
    display: inline-block; font-family: 'Space Mono', monospace;
    font-size: 0.78rem; letter-spacing: 0.1em; text-transform: uppercase;
    padding: 0.5rem 1rem; border-radius: 6px; border: 1px solid; margin: 0.35rem;
}}
.t-card {{
    background: {C["surface"]}; border: 1px solid {C["border"]};
    border-radius: 10px; padding: 1.5rem 2rem; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 1.5rem;
    transition: border-color 0.2s, transform 0.15s;
}}
.t-card:hover {{ border-color: {C["border2"]}; transform: translateX(5px); }}

.hr {{ height: 1px; background: {C["border"]}; margin: 3rem 0; }}
.ins-footer {{
    margin-top: 4rem; padding-top: 2rem; border-top: 1px solid {C["border"]};
    display: flex; justify-content: space-between;
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem; color: {C["text_faint"]}; letter-spacing: 0.1em;
}}
.alert {{
    background: {'#1a1212' if IS_DARK else '#fff5f3'};
    border: 1px solid {C["rust"]}55; border-left: 4px solid {C["rust"]};
    border-radius: 6px; padding: 1.2rem 1.6rem;
    font-family: 'Space Mono', monospace; font-size: 0.9rem;
    color: {C["rust"]}; margin: 1rem 0;
}}
.empty-st {{ text-align: center; padding: 7rem 0; }}
.empty-ico {{
    font-family: 'Syne', sans-serif; font-size: 5rem; font-weight: 800;
    color: {C["border2"]}; margin-bottom: 1.5rem;
}}
.empty-lbl {{
    font-family: 'Space Mono', monospace; font-size: 0.85rem;
    letter-spacing: 0.2em; text-transform: uppercase; color: {C["text_faint"]};
}}
#MainMenu, footer, header {{ visibility: hidden; }}
div[data-testid="stDecoration"] {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# ─── Helpers ─────────────────────────────────────────────────────────────────
def score_color(s):
    return C["sage"] if s >= 70 else (C["amber"] if s >= 50 else C["rust"])

def sent_color(v):
    return C["sage"] if v > 0.2 else (C["rust"] if v < -0.2 else C["text_dim"])

def trend_arrow(v):
    return "↑" if v > 0.05 else ("↓" if v < -0.05 else "→")

def risk_pal(lvl):
    return {"High":   (C["rust"],  C["surface2"]),
            "Medium": (C["amber"], C["surface2"]),
            "Low":    (C["sage"],  C["surface2"])}.get(lvl, (C["text_dim"], C["surface2"]))

def fmt(v):
    return f"{v:+.3f}" if v != 0 else "0.000"

def px(hex_str):
    h = hex_str.strip()
    if h.startswith("#") and len(h) > 7:
        h = h[:7]
    return h

def do_analyze(keyword, limit):
    try:
        r = requests.get(f"{API_BASE}/analyze", params={"keyword": keyword, "limit": limit}, timeout=90)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.session_state["conn_err"] = True
        return None
    except Exception as e:
        st.session_state["api_err"] = str(e)
        return None

def do_trending():
    try:
        r = requests.get(f"{API_BASE}/trending", timeout=90)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and all("keyword" in d for d in data):
            return data
        return None
    except requests.exceptions.ConnectionError:
        st.session_state["conn_err"] = True
        return None
    except Exception as e:
        st.session_state["trend_err"] = str(e)
        return None

def save_history(data):
    hist = st.session_state["history"]
    if not any(h["keyword"] == data["keyword"] for h in hist):
        hist.insert(0, {k: data[k] for k in
            ("keyword", "launch_score", "risk_level", "recommendation", "average_sentiment")})
        if len(hist) > 12:
            hist.pop()

# ═══════════════════════════════════════════════════════════════════
# CENTERED HEADER
# ═══════════════════════════════════════════════════════════════════
col_left, col_mid, col_right = st.columns([1.5, 7, 1.5])

with col_mid:
    st.markdown(f"""
<div style="text-align: center; padding: 2.5rem 0 3.5rem 0;">
  <div style="display: inline-flex; align-items: center; justify-content: center; gap: 1.2rem;">
    <span style="font-family:'Syne',sans-serif; font-weight:800; font-size:4.8rem; color:{C['amber']}; line-height:1; letter-spacing:0.02em;">INSYTE</span>
    <span style="font-family:'Space Mono',monospace; font-size:0.95rem; color:{C['text_dim']}; border:1px solid {C['border2']}; padding:6px 14px; border-radius:6px; transform:translateY(-8px);">v5.0</span>
  </div>
  <div style="margin-top:1.5rem; font-family:'Space Mono',monospace; font-size:0.9rem; color:{C['text_faint']}; letter-spacing:0.2em; text-transform:uppercase;">
    Real-Time Market Intelligence · NLP Powered · Multilingual
  </div>
</div>
""", unsafe_allow_html=True)

with col_right:
    st.markdown('<div style="height:3rem;"></div>', unsafe_allow_html=True)
    if st.button("☀ Light" if IS_DARK else "◑ Dark", use_container_width=True):
        st.session_state["dark_mode"] = not IS_DARK
        st.rerun()

st.markdown(f'<div style="height:1px; background:{C["border"]}; margin-bottom:3rem;"></div>', unsafe_allow_html=True)

if st.session_state["conn_err"]:
    st.markdown(
        f'<div class="alert">⚠  Cannot connect to backend — ensure FastAPI is running on port 8000: '
        f'<code>uvicorn backend.main:app --reload</code></div>',
        unsafe_allow_html=True)

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab_a, tab_t, tab_h = st.tabs(["◈  Analyze", "⬡  Trending", "◷  History"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALYZE
# ══════════════════════════════════════════════════════════════════════════════
with tab_a:
    st.markdown('<div class="sec-lbl">01 — Search Query</div>', unsafe_allow_html=True)

    # ── Search Input ──
    query = st.text_input(
        "Search Query",
        placeholder="Enter a product, idea, company or topic to analyze...",
        value=st.session_state["query"],
        label_visibility="collapsed"
    )

    st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)

    # ── Slider + Button Row ──
    col_slider, col_btn = st.columns([5, 1.5])

    with col_slider:
        limit = st.slider("Articles to fetch", 20, 100, st.session_state.lim_val, 10)
        if limit != st.session_state.lim_val:
            st.session_state.lim_val = limit
            st.rerun()

        # Dynamic coloured coverage bar
        sl_c  = slider_color(limit)
        pct   = round((limit - 20) / 80 * 100)
        label = "High Coverage" if limit >= 70 else ("Medium Coverage" if limit >= 45 else "Quick Scan")
        
        st.markdown(f"""
<div style="display:flex; align-items:center; gap:1.5rem; margin-top:0.8rem;">
  <div style="flex:1; height:8px; background:{C['border2']}; border-radius:4px; overflow:hidden;">
    <div style="width:{pct}%; height:100%; background:{sl_c}; border-radius:4px; transition:width 0.3s ease;"></div>
  </div>
  <span style="font-family:'Space Mono',monospace; font-size:0.85rem; color:{sl_c}; font-weight:700; letter-spacing:0.08em; min-width:200px; text-align:right;">
    {limit} articles · {label}
  </span>
</div>
""", unsafe_allow_html=True)

    with col_btn:
        st.markdown('<div class="run-btn">', unsafe_allow_html=True)
        run = st.button("▶ RUN ANALYSIS", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:4rem;"></div>', unsafe_allow_html=True)

    # ── Quick Presets ──
    st.markdown('<div class="sec-lbl" style="margin-bottom:1.5rem;">Quick Presets</div>', unsafe_allow_html=True)

    preset_labels = [
        "AI STARTUP", "ELECTRIC VEHICLES", "CLIMATE TECH",
        "WEB3", "FINTECH", "SAAS TOOLS", "BIOTECH"
    ]

    preset_cols = st.columns(len(preset_labels), gap="medium")

    for i, label in enumerate(preset_labels):
        with preset_cols[i]:
            if st.button(label, use_container_width=True, key=f"pre_{i}"):
                st.session_state["query"] = label
                st.rerun()

    # ── Run Logic ──
    final_kw = query.strip() if query else st.session_state["query"].strip()
    
    if run and final_kw:
        st.session_state["query"] = final_kw # Sync
        st.session_state["conn_err"] = False
        st.session_state["api_err"]  = ""
        with st.spinner(f"Analyzing **{final_kw}**..."):
            data = do_analyze(final_kw, limit)
        if data:
            st.session_state["result"] = data
            save_history(data)
    elif run:
        st.markdown('<div class="alert">⚠  Please enter a keyword to begin.</div>', unsafe_allow_html=True)

    if st.session_state["api_err"]:
        st.markdown(f'<div class="alert">⚠  API error: {st.session_state["api_err"]}</div>', unsafe_allow_html=True)

    # ── Results Rendering ──
    d = st.session_state["result"]

    if d:
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sec-lbl">02 — Results · {d["keyword"]}</div>', unsafe_allow_html=True)

        ca, cb, cc = st.columns([2.5, 4, 2.5])

        with ca:
            sc     = d["launch_score"]
            sc_col = score_color(sc)
            conf_p = int(d["confidence"] * 100)
            st.markdown(f"""
<div class="score-block">
  <div class="m-tile-lbl">Launch Readiness Score</div>
  <div class="score-num" style="color:{sc_col};">{sc}</div>
  <div class="score-sub">/ 100 points</div>
  <div class="m-tile-lbl">Data Confidence</div>
  <div style="height:8px; background:{C['border2']}; border-radius:4px; overflow:hidden; margin-bottom:0.8rem;">
    <div style="width:{conf_p}%; height:100%; background:{sc_col}; border-radius:4px;"></div>
  </div>
  <div style="font-family:'Space Mono',monospace; font-size:0.8rem; color:{C['text_dim']}; margin-bottom:1.8rem;">
    {conf_p}% confidence
  </div>
  <div class="rec-txt" style="color:{sc_col};">{d['recommendation']}</div>
</div>
""", unsafe_allow_html=True)

        with cb:
            dist  = d["distribution"]
            tot_d = dist["positive"] + dist["neutral"] + dist["negative"] or 1
            pos_p = round(dist["positive"] / tot_d * 100, 1)
            neu_p = round(dist["neutral"]  / tot_d * 100, 1)
            neg_p = round(dist["negative"] / tot_d * 100, 1)

            fig_dist = go.Figure()
            for name, val, col, fnt in [
                ("Positive", pos_p, px(C["sage"]),    C["bg"]),
                ("Neutral",  neu_p, px(C["border2"]), C["text_dim"]),
                ("Negative", neg_p, px(C["rust"]),    "#fff"),
            ]:
                fig_dist.add_trace(go.Bar(
                    name=name, x=[val], y=[""], orientation="h",
                    marker_color=col,
                    text=[f"{val}%"], textposition="inside",
                    insidetextanchor="middle",
                    textfont=dict(family="Space Mono", size=11, color=fnt),
                    hovertemplate=f"{name}: %{{x:.1f}}%<extra></extra>",
                ))
            fig_dist.update_layout(
                barmode="stack", height=80,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor=C["plot_bg"], plot_bgcolor=C["plot_bg"],
                showlegend=False,
                xaxis=dict(visible=False, range=[0, 100]),
                yaxis=dict(visible=False),
            )

            emo      = d.get("emotions", {})
            emo_lbls = list(emo.keys())
            emo_vals = list(emo.values())
            emo_cols = [px(EMOTION_COLORS.get(e, C["text_dim"])) for e in emo_lbls]

            fig_donut = go.Figure(go.Pie(
                labels=emo_lbls, values=emo_vals, hole=0.62,
                marker=dict(colors=emo_cols, line=dict(color=px(C["bg"]), width=2)),
                textinfo="none",
                hovertemplate="%{label}: %{percent}<extra></extra>",
            ))
            fig_donut.update_layout(
                height=260,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor=C["plot_bg"],
                showlegend=True,
                legend=dict(orientation="v", x=1.0, y=0.5,
                            font=dict(family="Space Mono", size=10, color=px(C["text_dim"])),
                            bgcolor="rgba(0,0,0,0)"),
            )

            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-ttl">Sentiment Distribution</div>', unsafe_allow_html=True)
            st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""
<div style="display:flex; gap:2rem; margin:0.8rem 0 1.8rem 0;">
  <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:{C['sage']};">● {dist['positive']} Pos</span>
  <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:{C['text_dim']};">● {dist['neutral']} Neu</span>
  <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:{C['rust']};">● {dist['negative']} Neg</span>
</div>
<div class="panel-ttl">Emotion Breakdown</div>
""", unsafe_allow_html=True)
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

        with cc:
            rc, rbg = risk_pal(d["risk_level"])
            avg_col = sent_color(d["average_sentiment"])
            t_val   = d["sentiment_trend"]
            t_col   = C["sage"] if t_val > 0.05 else (C["rust"] if t_val < -0.05 else C["text_dim"])

            st.markdown(f"""
<div class="panel">
  <div class="panel-ttl">Risk & Signals</div>

  <div class="m-tile-lbl">Risk Level</div>
  <div class="risk-bdg" style="border-color:{rc}; color:{rc}; background:{rbg}; margin-bottom:2rem;">
    <span style="width:8px; height:8px; border-radius:50%; background:{rc}; display:inline-block;"></span>
    {d['risk_level']} Risk
  </div>

  <div class="m-tile-lbl" style="margin-top:1.5rem;">Average Sentiment</div>
  <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:2.8rem; color:{avg_col}; line-height:1; margin-bottom:0.4rem;">
    {fmt(d['average_sentiment'])}
  </div>
  <div class="m-tile-sub">−1.0 to +1.0 scale</div>

  <div class="m-tile-lbl" style="margin-top:1.8rem;">Sentiment Trend</div>
  <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:2.8rem; color:{t_col}; line-height:1; margin-bottom:0.4rem;">
    {trend_arrow(t_val)} {abs(round(t_val,3))}
  </div>
  <div class="m-tile-sub">{'Improving' if t_val > 0.05 else 'Declining' if t_val < -0.05 else 'Stable'} over time</div>

  <div class="m-tile-lbl" style="margin-top:1.8rem;">Total Articles</div>
  <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:2.8rem; color:{C['amber']}; line-height:1;">
    {d['total_posts']}
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        # ── KPI Tiles ──
        st.markdown('<div class="sec-lbl">03 — Key Metrics</div>', unsafe_allow_html=True)
        t1, t2, t3, t4 = st.columns(4)
        sc_col  = score_color(d["launch_score"])
        avg_col = sent_color(d["average_sentiment"])
        rc2, _  = risk_pal(d["risk_level"])

        metrics_data = [
            (t1, "Launch Score",      str(d["launch_score"]),       "out of 100", f"linear-gradient(90deg,{C['amber']},{C['amber']}66)", sc_col),
            (t2, "Articles Analyzed", str(d["total_posts"]),        "data points", f"linear-gradient(90deg,{C['slate']},{C['slate']}66)", C["slate"]),
            (t3, "Avg Sentiment",     fmt(d["average_sentiment"]),  "−1.0 to +1.0", f"linear-gradient(90deg,{avg_col},{avg_col}66)", avg_col),
            (t4, "Risk Level",        d["risk_level"],              f"{d['distribution'].get('positive_pct', 0)}% positive", f"linear-gradient(90deg,{rc2},{rc2}66)", rc2),
        ]

        for col, lbl, val, sub, grad, vc in metrics_data:
            with col:
                st.markdown(f"""
<div class="m-tile">
  <div class="m-tile-bar" style="background:{grad};"></div>
  <div class="m-tile-lbl">{lbl}</div>
  <div class="m-tile-val" style="color:{vc};">{val}</div>
  <div class="m-tile-sub">{sub}</div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        # ── Signals Row ──
        st.markdown('<div class="sec-lbl">04 — Signals</div>', unsafe_allow_html=True)
        r1, r2 = st.columns([2.5, 3])

        with r1:
            kws   = d.get("top_keywords", [])
            pills = "".join(
                f'<span class="kw-pill" style="border-color:{PILL_COLORS[i%5]}55; color:{PILL_COLORS[i%5]}; background:{PILL_COLORS[i%5]}11;">{kw}</span>'
                for i, kw in enumerate(kws)
            )
            conf_p2 = int(d["confidence"] * 100)
            st.markdown(f"""
<div class="panel">
  <div class="panel-ttl">Top Keywords</div>
  <div style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-bottom:2rem;">{pills}</div>
  <div class="panel-ttl" style="margin-top:0.5rem;">Analysis Confidence</div>
  <div style="height:8px; background:{C['border2']}; border-radius:4px; overflow:hidden; margin-bottom:0.8rem;">
    <div style="width:{conf_p2}%; height:100%; background:linear-gradient(90deg,{C['slate']},{C['sage']}); border-radius:4px;"></div>
  </div>
  <div style="font-family:'Space Mono',monospace; font-size:0.8rem; color:{C['text_dim']};">
    {conf_p2}% — based on {d['total_posts']} articles
  </div>
</div>
""", unsafe_allow_html=True)

        with r2:
            avg   = d["average_sentiment"]
            g_col = px(sent_color(avg))
            g_val = round((avg + 1) / 2 * 100, 1)

            try:
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=g_val,
                    number={"suffix": "", "font": {"family": "Syne", "size": 38, "color": g_col}},
                    gauge={
                        "axis": {"range": [0, 100], "tickfont": {"size": 10, "color": px(C["text_dim"])}, "tickcolor": px(C["border2"]), "nticks": 5},
                        "bar": {"color": g_col, "thickness": 0.3},
                        "bgcolor": px(C["border"]),
                        "steps": [
                            {"range": [0, 33],   "color": px(C["rust"])},
                            {"range": [33, 66],  "color": px(C["amber"])},
                            {"range": [66, 100], "color": px(C["sage"])},
                        ],
                        "threshold": {"line": {"color": g_col, "width": 3}, "thickness": 0.75, "value": g_val},
                    },
                ))
                fig_g.update_layout(
                    height=280,
                    margin=dict(l=30, r=30, t=30, b=15),
                    paper_bgcolor=C["plot_bg"],
                    font=dict(family="Space Mono", color=px(C["text_dim"])),
                )
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown('<div class="panel-ttl">Sentiment Gauge</div>', unsafe_allow_html=True)
                st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})
                st.markdown(f"""
<div style="display:flex; justify-content:space-between; font-family:'Space Mono',monospace; font-size:0.75rem; margin-top:-0.5rem;">
  <span style="color:{C['rust']};">◀ Negative</span>
  <span style="color:{C['text_dim']};">Neutral</span>
  <span style="color:{C['sage']};">Positive ▶</span>
</div>
""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as chart_err:
                st.markdown(f'<div class="alert">Chart error: {chart_err}</div>', unsafe_allow_html=True)

    else:
        st.markdown(f"""
<div class="empty-st">
  <div class="empty-ico" style="color:{C['border2']}">◈</div>
  <div class="empty-lbl">Enter a keyword above to begin analysis</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TRENDING
# ══════════════════════════════════════════════════════════════════════════════
with tab_t:
    st.markdown('<div class="sec-lbl">Live Trending Keywords</div>', unsafe_allow_html=True)

    fc1, _ = st.columns([2, 6])
    with fc1:
        fetch_btn = st.button("⬡  Fetch Trending Now", key="fetch_btn", use_container_width=True)

    if fetch_btn:
        st.session_state["conn_err"]  = False
        st.session_state["trend_err"] = ""
        with st.spinner("Fetching trending keywords from live news..."):
            result = do_trending()
        if result is not None:
            st.session_state["trending"] = result
        elif not st.session_state["conn_err"]:
            st.session_state["trend_err"] = "No data returned — check your backend service."

    if st.session_state.get("trend_err"):
        st.markdown(f'<div class="alert">⚠  {st.session_state["trend_err"]}</div>', unsafe_allow_html=True)

    trends = st.session_state.get("trending")

    if trends and isinstance(trends, list):
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        for i, item in enumerate(trends):
            score  = item.get("score", 0)
            vol    = item.get("volume", 0)
            sc     = sent_color(score)
            rc     = RANK_COLORS[i % len(RANK_COLORS)]
            num    = f"0{i+1}" if i + 1 < 10 else str(i + 1)
            slabel = "Positive" if score > 0.2 else ("Negative" if score < -0.2 else "Neutral")

            st.markdown(f"""
<div class="t-card">
  <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.6rem; color:{rc}; min-width:3.2rem;">{num}</div>
  <div style="font-family:'Syne',sans-serif; font-weight:700; font-size:1.25rem; flex:1;">
    {item['keyword'].upper()}
  </div>
  <div style="font-family:'Space Mono',monospace; font-size:0.8rem; padding:0.4rem 1rem; border-radius:4px; background:{sc}18; color:{sc}; border:1px solid {sc}44; white-space:nowrap;">
    {slabel} · {fmt(score)}
  </div>
  <div style="font-family:'Space Mono',monospace; font-size:0.8rem; color:{C['text_dim']}; min-width:120px; text-align:right;">
    {vol} articles
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-lbl">Sentiment vs Volume</div>', unsafe_allow_html=True)
        kws_t    = [t["keyword"] for t in trends]
        scores_t = [t.get("score", 0) for t in trends]
        vols_t   = [t.get("volume", 0) for t in trends]
        bar_cols = [px(sent_color(s)) for s in scores_t]

        try:
            fig_tr = go.Figure()
            fig_tr.add_trace(go.Bar(
                name="Volume", x=kws_t, y=vols_t,
                marker_color=px(C["slate"]), opacity=0.5, yaxis="y2",
                hovertemplate="%{x}<br>Volume: %{y}<extra></extra>",
            ))
            fig_tr.add_trace(go.Scatter(
                name="Sentiment", x=kws_t, y=scores_t,
                mode="lines+markers",
                line=dict(color=px(C["amber"]), width=2.5),
                marker=dict(color=bar_cols, size=12, line=dict(color=px(C["bg"]), width=1.5)),
                hovertemplate="%{x}<br>Sentiment: %{y:.3f}<extra></extra>",
            ))
            fig_tr.add_hline(y=0, line_dash="dot", line_color=px(C["border2"]), line_width=1.5)
            fig_tr.update_layout(
                height=400,
                paper_bgcolor=C["plot_bg"], plot_bgcolor=C["plot_bg"],
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family="Space Mono", size=11, color=px(C["text_dim"])),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor=px(C["grid"]), tickfont=dict(size=10)),
                yaxis=dict(title="Sentiment", gridcolor=px(C["grid"]), zerolinecolor=px(C["border2"]), tickfont=dict(size=10)),
                yaxis2=dict(title="Volume", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10)),
                barmode="overlay",
            )
            st.plotly_chart(fig_tr, use_container_width=True, config={"displayModeBar": False})
        except Exception as chart_err:
            st.markdown(f'<div class="alert">Chart error: {chart_err}</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-lbl">Quick Analyze from Trending</div>', unsafe_allow_html=True)
        n = min(len(trends), 4)
        qa_cols = st.columns(n)
        for i, item in enumerate(trends[:n]):
            with qa_cols[i]:
                if st.button(f"▶  {item['keyword']}", key=f"qa_{i}", use_container_width=True):
                    st.session_state["query"] = item["keyword"]
                    with st.spinner(f"Analyzing {item['keyword']}..."):
                        data = do_analyze(item["keyword"], 80)
                    if data:
                        st.session_state["result"] = data
                        save_history(data)
                        st.success("Done — switch to Analyze tab.")
    else:
        st.markdown(f"""
<div class="empty-st">
  <div class="empty-ico" style="color:{C['border2']}">⬡</div>
  <div class="empty-lbl">Click "Fetch Trending Now" to load live data</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTORY
# ══════════════════════════════════════════════════════════════════════════════
with tab_h:
    st.markdown('<div class="sec-lbl">Session History</div>', unsafe_allow_html=True)
    history = st.session_state.get("history", [])

    if history:
        if len(history) >= 2:
            st.markdown('<div class="sec-lbl">Score Comparison</div>', unsafe_allow_html=True)
            h_kws    = [h["keyword"] for h in history]
            h_scores = [h["launch_score"] for h in history]
            h_cols   = [px(score_color(s)) for s in h_scores]

            try:
                fig_h = go.Figure(go.Bar(
                    x=h_kws, y=h_scores, marker_color=h_cols,
                    text=h_scores, textposition="outside",
                    textfont=dict(family="Space Mono", size=11, color=px(C["text_dim"])),
                    hovertemplate="%{x}<br>Score: %{y}<extra></extra>",
                ))
                for yval, col, lbl in [(70, px(C["sage"]), "Strong"), (50, px(C["amber"]), "Moderate")]:
                    fig_h.add_hline(y=yval, line_dash="dot", line_color=col,
                                    annotation_text=lbl, annotation_position="right",
                                    annotation_font=dict(size=10, color=col))
                fig_h.update_layout(
                    height=320,
                    paper_bgcolor=C["plot_bg"], plot_bgcolor=C["plot_bg"],
                    margin=dict(l=0, r=80, t=20, b=0),
                    font=dict(family="Space Mono", size=11, color=px(C["text_dim"])),
                    showlegend=False,
                    xaxis=dict(gridcolor=px(C["grid"]), tickfont=dict(size=10)),
                    yaxis=dict(range=[0, 120], gridcolor=px(C["grid"]), tickfont=dict(size=10)),
                )
                st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})
            except Exception as chart_err:
                st.markdown(f'<div class="alert">Chart error: {chart_err}</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        for h in history:
            sc_col  = score_color(h["launch_score"])
            rc, rbg = risk_pal(h["risk_level"])
            ac      = sent_color(h["average_sentiment"])
            st.markdown(f"""
<div class="t-card" style="padding:1.8rem 2.2rem;">
  <div style="flex:1;">
    <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.35rem; margin-bottom:0.4rem;">
      {h['keyword'].upper()}
    </div>
    <div style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:{C['text_dim']};">
      {h['recommendation']}
    </div>
  </div>
  <div style="text-align:center; min-width:90px;">
    <div class="m-tile-lbl">Score</div>
    <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.9rem; color:{sc_col};">
      {h['launch_score']}
    </div>
  </div>
  <div style="text-align:center; min-width:110px;">
    <div class="m-tile-lbl">Sentiment</div>
    <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.45rem; color:{ac};">
      {fmt(h['average_sentiment'])}
    </div>
  </div>
  <div class="risk-bdg" style="border-color:{rc}; color:{rc}; background:{rbg}; min-width:130px; justify-content:center;">
    {h['risk_level']} Risk
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        cl1, _ = st.columns([2.5, 5.5])
        with cl1:
            if st.button("✕  Clear History", key="clr_hist", use_container_width=True):
                st.session_state["history"] = []
                st.rerun()
    else:
        st.markdown(f"""
<div class="empty-st">
  <div class="empty-ico" style="color:{C['border2']}">◷</div>
  <div class="empty-lbl">No analyses yet — results appear here automatically</div>
</div>
""", unsafe_allow_html=True)

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ins-footer">
  <span>INSYTE v5.0 · Real-Time Market Intelligence Platform</span>
  <span>Powered by NewsAPI · BERT · DistilBERT</span>
</div>
""", unsafe_allow_html=True)