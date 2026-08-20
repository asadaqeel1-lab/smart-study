import streamlit as st
import requests, uuid, json, io, datetime, html

st.set_page_config(page_title="Smart Study Recommender", page_icon="🎓", layout="wide",
                   initial_sidebar_state="expanded")

API_BASE = "http://localhost:5000"

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');
:root{--bg:#080c18;--surface:#0d1226;--card:#111827;--card2:#0f172a;
--border:rgba(99,102,241,0.18);--purple:#7c3aed;--purple2:#a855f7;
--blue:#3b82f6;--cyan:#06b6d4;--green:#10b981;--pink:#ec4899;
--orange:#f59e0b;--text:#f1f5f9;--muted:#64748b;--muted2:#94a3b8;}
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:var(--bg)!important;color:var(--text)!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:0!important;padding-bottom:0!important;max-width:100%!important;}
.main .block-container{padding-left:2rem!important;padding-right:2rem!important;}
[data-testid="stAppViewContainer"]{overflow-x:hidden;}
[data-testid="stVerticalBlock"]{gap:0.5rem!important;}
section[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important;width:230px!important;}
section[data-testid="stSidebar"]>div{padding:0!important;}
section[data-testid="stSidebar"] *{color:var(--muted2)!important;}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{color:var(--text)!important;}
.stTextInput input{background:rgba(15,23,42,0.8)!important;border:1px solid rgba(99,102,241,0.25)!important;
border-radius:12px!important;color:var(--text)!important;font-size:15px!important;padding:14px 18px!important;transition:all 0.2s!important;}
.stTextInput input:focus{border-color:var(--purple)!important;box-shadow:0 0 0 3px rgba(124,58,237,0.15)!important;}
.stButton>button{background:linear-gradient(135deg,#7c3aed,#a855f7)!important;border:none!important;
border-radius:12px!important;color:white!important;font-size:14px!important;font-weight:600!important;
min-height:48px!important;padding:10px 16px!important;display:flex!important;align-items:center!important;
justify-content:center!important;white-space:nowrap!important;line-height:1!important;transition:all 0.2s!important;
box-shadow:0 4px 15px rgba(124,58,237,0.35)!important;}
.stButton>button div[data-testid="stMarkdownContainer"]{display:flex!important;align-items:center!important;justify-content:center!important;}
.stButton>button div[data-testid="stMarkdownContainer"] p,.stButton>button p{margin:0!important;white-space:nowrap!important;line-height:1!important;}
.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 6px 25px rgba(124,58,237,0.5)!important;}
section[data-testid="stSidebar"] .stButton>button{background:rgba(99,102,241,0.08)!important;
border:1px solid rgba(99,102,241,0.15)!important;border-radius:10px!important;color:#94a3b8!important;
font-size:13px!important;font-weight:500!important;padding:9px 14px!important;text-align:left!important;
justify-content:flex-start!important;box-shadow:none!important;width:100%!important;}
section[data-testid="stSidebar"] .stButton>button:hover{background:rgba(124,58,237,0.15)!important;color:white!important;}
div[data-baseweb="select"]>div{background:rgba(15,23,42,0.8)!important;border:1px solid rgba(99,102,241,0.25)!important;
border-radius:10px!important;color:var(--text)!important;}
div[data-baseweb="select"] *{background:#0f172a!important;color:var(--text)!important;}
.stSlider [role="slider"]{background:linear-gradient(135deg,var(--purple),var(--purple2))!important;}
[data-testid="metric-container"]{background:var(--card)!important;border:1px solid var(--border)!important;
border-radius:16px!important;padding:20px 24px!important;}
[data-testid="metric-container"] label{color:var(--muted2)!important;font-size:12px!important;font-weight:500!important;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{color:white!important;font-family:'Space Grotesk',sans-serif!important;}
.resource-card:hover{transform:translateY(-4px);border-color:rgba(124,58,237,0.4)!important;
box-shadow:0 10px 35px rgba(124,58,237,0.22);}
.top-nav{margin-bottom:18px;padding:10px;background:rgba(15,23,42,0.62);border:1px solid var(--border);border-radius:14px;}
.top-nav [data-testid="stHorizontalBlock"]{gap:8px!important;}
div[class*="st-key-top_nav_"] button{min-height:40px!important;padding:9px 14px!important;background:transparent!important;
border:1px solid transparent!important;box-shadow:none!important;color:#94a3b8!important;font-size:13px!important;
font-weight:600!important;border-radius:10px!important;}
div[class*="st-key-top_nav_"] button:hover{background:rgba(124,58,237,0.15)!important;color:white!important;
box-shadow:none!important;transform:none!important;border-color:rgba(124,58,237,0.25)!important;}
.top-nav-active{min-height:40px;display:flex;align-items:center;justify-content:center;border-radius:10px;
background:linear-gradient(135deg,rgba(124,58,237,0.28),rgba(168,85,247,0.16));border:1px solid rgba(124,58,237,0.35);
color:white;font-size:13px;font-weight:700;}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
</style>
""", unsafe_allow_html=True)

# ─── Config ───────────────────────────────────────────────────────────────────
LEVEL_CFG = {
    "Beginner":      {"color":"#10b981","bg":"rgba(16,185,129,0.1)","border":"rgba(16,185,129,0.3)"},
    "Introductory":  {"color":"#06b6d4","bg":"rgba(6,182,212,0.1)","border":"rgba(6,182,212,0.3)"},
    "Intermediate":  {"color":"#3b82f6","bg":"rgba(59,130,246,0.1)","border":"rgba(59,130,246,0.3)"},
    "Advanced":      {"color":"#8b5cf6","bg":"rgba(139,92,246,0.1)","border":"rgba(139,92,246,0.3)"},
    "Expert":        {"color":"#f59e0b","bg":"rgba(245,158,11,0.1)","border":"rgba(245,158,11,0.3)"},
    "All Levels":    {"color":"#64748b","bg":"rgba(100,116,139,0.1)","border":"rgba(100,116,139,0.3)"},
}
TYPE_CFG = {
    "Course": {"color":"#a855f7","bg":"rgba(168,85,247,0.1)","border":"rgba(168,85,247,0.3)","icon":"📚"},
    "Book":   {"color":"#06b6d4","bg":"rgba(6,182,212,0.1)","border":"rgba(6,182,212,0.3)","icon":"📖"},
    "Video":  {"color":"#ec4899","bg":"rgba(236,72,153,0.1)","border":"rgba(236,72,153,0.3)","icon":"🎥"},
    "Article":{"color":"#10b981","bg":"rgba(16,185,129,0.1)","border":"rgba(16,185,129,0.3)","icon":"📄"},
}
QUICK_TOPICS = ["Python","Machine Learning","Web Development","Data Science",
                "Deep Learning","NLP","Computer Vision","Cybersecurity","Cloud Computing","Blockchain"]
NAV_ITEMS = [
    {"label":"Search","key":"search"},
    {"label":"Bookmarks","key":"bookmarks"},
    {"label":"Compare","key":"compare"},
    {"label":"Analytics","key":"analytics"},
    {"label":"History","key":"history"},
]

# ─── Session state ─────────────────────────────────────────────────────────
for k,v in [("results",[]),("last_query",""),("history",[]),("page","search"),
            ("bookmarks",[]),("compare_list",[]),("predicted_level",""),
            ("confidence",0.0),("session_id", str(uuid.uuid4())[:12])]:
    if k not in st.session_state: st.session_state[k] = v

SID = st.session_state.session_id
try:
    requested_page = st.query_params.get("page")
except Exception:
    try:
        requested_page = st.experimental_get_query_params().get("page", [None])[0]
    except Exception:
        requested_page = None
if isinstance(requested_page, list):
    requested_page = requested_page[0] if requested_page else None
if requested_page in {item["key"] for item in NAV_ITEMS}:
    st.session_state.page = requested_page

def set_page(page_key):
    st.session_state.page = page_key
    try:
        st.query_params["page"] = page_key
    except Exception:
        try:
            st.experimental_set_query_params(page=page_key)
        except Exception:
            pass

# ─── API helpers ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_stats():
    try: r = requests.get(f"{API_BASE}/stats", timeout=4); return r.json() if r.ok else {}
    except: return {}

@st.cache_data(ttl=30)
def fetch_trending():
    try: r = requests.get(f"{API_BASE}/trending?n=8", timeout=4); return r.json() if r.ok else []
    except: return []

def fetch_recs(query, level, top_n):
    try:
        r = requests.post(f"{API_BASE}/recommend",
            json={"query":query,"level":level,"top_n":top_n,"session_id":SID}, timeout=12)
        if r.ok:
            d = r.json()
            return d.get("results",[]), None, d.get("predicted_level",""), d.get("confidence",0.0)
        return [], f"Server error {r.status_code}", "", 0.0
    except requests.exceptions.ConnectionError:
        return [], "❌ Backend offline — run: python app.py", "", 0.0
    except Exception as e: return [], str(e), "", 0.0

def fetch_model_details():
    try: r = requests.get(f"{API_BASE}/model-details", timeout=5); return r.json() if r.ok else {}
    except: return {}

def fetch_similar(title):
    try:
        r = requests.post(f"{API_BASE}/similar", json={"title":title,"top_n":4}, timeout=8)
        return r.json().get("results",[]) if r.ok else []
    except: return []

def add_bookmark(course):
    try:
        requests.post(f"{API_BASE}/bookmark", json={"session_id":SID,
            "course_title":course["title"],"course_level":course.get("level",""),
            "course_topic":course.get("topic",""),"course_link":course.get("link",""),
            "score":course.get("score",0)}, timeout=4)
        bm = {"title":course["title"],"level":course.get("level",""),
              "topic":course.get("topic",""),"link":course.get("link",""),
              "score":course.get("score",0)}
        if not any(b["title"]==bm["title"] for b in st.session_state.bookmarks):
            st.session_state.bookmarks.append(bm)
    except: pass

def export_csv(query, level, top_n):
    try:
        r = requests.post(f"{API_BASE}/export/results",
            json={"query":query,"level":level,"top_n":top_n}, timeout=15)
        return r.json().get("csv","") if r.ok else ""
    except: return ""

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:24px 20px 16px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
        <div style="width:36px;height:36px;background:linear-gradient(135deg,#7c3aed,#06b6d4);
          border-radius:10px;display:flex;align-items:center;justify-content:center;
          font-size:18px;box-shadow:0 4px 15px rgba(124,58,237,0.4);">🎓</div>
        <div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:white;">
            SMART <span style="color:#a855f7;">STUDY</span></div>
          <div style="font-size:9px;color:#475569;letter-spacing:1.5px;">RESOURCE RECOMMENDER v4.0</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    for item in NAV_ITEMS:
        is_active = st.session_state.page == item["key"]
        badge = ""
        if item["key"]=="bookmarks" and st.session_state.bookmarks:
            badge = f'<span style="background:#7c3aed;color:white;border-radius:10px;padding:1px 7px;font-size:10px;margin-left:auto;">{len(st.session_state.bookmarks)}</span>'
        if is_active:
            st.markdown(f"""<div style="margin:2px 12px;padding:10px 16px;
              background:linear-gradient(135deg,rgba(124,58,237,0.2),rgba(168,85,247,0.1));
              border:1px solid rgba(124,58,237,0.3);border-radius:10px;
              display:flex;align-items:center;gap:10px;">
              <span style="color:white;font-weight:600;font-size:14px;">{item['label']}</span>
              {badge}</div>""", unsafe_allow_html=True)
        else:
            if st.button(item["label"], key=f'nav_{item["key"]}', use_container_width=True):
                set_page(item["key"]); st.rerun()

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    # Trending topics
    trending = fetch_trending()
    if trending:
        st.markdown("""<div style="padding:0 20px;margin-bottom:8px;">
          <span style="font-size:10px;font-weight:600;color:#475569;letter-spacing:1.5px;">🔥 TRENDING</span>
        </div>""", unsafe_allow_html=True)
        for t in trending[:5]:
            if st.button(f'{t["query"]} ({t["count"]}×)', key=f'tr_{t["query"]}', use_container_width=True):
                st.session_state["_quick"] = t["query"]; set_page("search"); st.rerun()
    else:
        st.markdown("""<div style="padding:0 20px;margin-bottom:8px;">
          <span style="font-size:10px;font-weight:600;color:#475569;letter-spacing:1.5px;">QUICK TOPICS</span>
        </div>""", unsafe_allow_html=True)
        for topic in QUICK_TOPICS[:6]:
            if st.button(topic, key=f"qt_{topic}", use_container_width=True):
                st.session_state["_quick"] = topic; set_page("search"); st.rerun()

    stats_s = fetch_stats()
    total = stats_s.get("total", 41322)
    st.markdown(f"""<div style="margin:16px 12px 0;padding:16px 18px;
      background:linear-gradient(135deg,rgba(124,58,237,0.15),rgba(6,182,212,0.08));
      border:1px solid rgba(124,58,237,0.2);border-radius:14px;">
      <div style="font-family:'Space Grotesk',sans-serif;font-size:26px;font-weight:800;
        color:white;line-height:1;">{total:,}+</div>
      <div style="font-size:12px;color:#64748b;margin-top:4px;">Total Resources Indexed</div>
      <div style="font-size:11px;color:#475569;margin-top:6px;">Session: {SID}</div>
    </div>""", unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
st.markdown('<div style="max-width:1200px;margin:0 auto;padding:24px 28px 40px;">', unsafe_allow_html=True)
page = st.session_state.page

st.markdown('<div class="top-nav">', unsafe_allow_html=True)
nav_cols = st.columns(len(NAV_ITEMS))
for nav_col, item in zip(nav_cols, NAV_ITEMS):
    nav_label = item["label"]
    if item["key"] == "bookmarks" and st.session_state.bookmarks:
        nav_label = f'{nav_label} ({len(st.session_state.bookmarks)})'
    with nav_col:
        if page == item["key"]:
            st.markdown(f'<div class="top-nav-active">{html.escape(nav_label)}</div>', unsafe_allow_html=True)
        elif st.button(nav_label, key=f'top_nav_{item["key"]}', use_container_width=True):
            set_page(item["key"]); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: SEARCH
# ══════════════════════════════════════════════════════════════════════════════
if page == "search":
    main_col, right_col = st.columns([3,1], gap="large")
    with main_col:
        # Hero
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0d1226 0%,#12163a 50%,#0d1226 100%);
          border:1px solid rgba(99,102,241,0.2);border-radius:20px;padding:32px 40px;
          margin-bottom:20px;position:relative;overflow:hidden;animation:fadeUp 0.5s ease;">
          <div style="position:absolute;top:-60px;right:120px;width:200px;height:200px;border-radius:50%;
            background:radial-gradient(circle,rgba(124,58,237,0.3),transparent 70%);pointer-events:none;"></div>
          <h1 style="font-family:'Space Grotesk',sans-serif;font-size:clamp(24px,3.5vw,38px);
            font-weight:800;line-height:1.15;margin:0;color:white;">
            Find Your <span style="background:linear-gradient(135deg,#7c3aed,#a855f7,#06b6d4);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">Perfect</span><br>Study Resources
          </h1>
        </div>""", unsafe_allow_html=True)

        # Search bar
        dq = st.session_state.pop("_quick","")
        sc1, sc2 = st.columns([5,1])
        with sc1:
            query = st.text_input("", value=dq,
                placeholder="e.g. Machine Learning, Python, Web Dev, Deep Learning...",
                label_visibility="collapsed", key="search_input")
        with sc2:
            search_btn = st.button("Search →", use_container_width=True)

        fc1, fc2, fc3 = st.columns([1.2, 1.2, 1])
        with fc1:
            level = st.selectbox("", ["All Levels","Beginner","Introductory","Intermediate","Advanced","Expert"],
                                 label_visibility="collapsed", key="level_sel")
        with fc2:
            top_n = st.slider("Results:", 3, 20, 8, label_visibility="visible")
        with fc3:
            sort_by = st.selectbox("Sort by", ["Best Match","Level","Alphabetical"],
                                   label_visibility="visible", key="sort_sel")

        do_search = search_btn or (dq and dq != st.session_state.get("_lq",""))
        if do_search:
            aq = query or dq
            if aq:
                with st.spinner(f"🔍 Searching {aq}..."):
                    res_list, err, pred_lvl, conf = fetch_recs(aq, level, top_n)
                st.session_state.results = res_list
                st.session_state.last_query = aq
                st.session_state["_lq"] = aq
                st.session_state.predicted_level = pred_lvl
                st.session_state.confidence = conf
                if res_list:
                    st.session_state.history.insert(0, {
                        "query":aq,"level":level,"count":len(res_list),
                        "results":res_list,"time":datetime.datetime.now().strftime("%I:%M %p"),
                        "predicted_level":pred_lvl})
                    st.session_state.history = st.session_state.history[:20]
                if err: st.error(err)

        results   = st.session_state.results
        last_q    = st.session_state.last_query
        pred_lvl  = st.session_state.predicted_level
        conf      = st.session_state.confidence

        if results:
            # Sort
            if sort_by == "Level":
                lo = {"Beginner":1,"Introductory":1,"All Levels":2,"Intermediate":3,"Advanced":4,"Expert":5}
                results = sorted(results, key=lambda r: lo.get(r.get("level",""),2))
            elif sort_by == "Alphabetical":
                results = sorted(results, key=lambda r: r.get("title",""))

            # Ranking banner
            level_note = f"Level filter: {pred_lvl}" if pred_lvl and pred_lvl not in ("All", "All Levels") else "No automatic level filter"
            st.markdown(f"""
            <div style="background:rgba(124,58,237,0.10);border:1px solid rgba(124,58,237,0.25);
              border-radius:10px;padding:10px 16px;margin-bottom:12px;
              display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
              <span style="font-size:13px;color:#a78bfa;font-weight:600;">Ranking</span>
              <span style="font-size:12px;color:#94a3b8;"><b style="color:#e2e8f0;">TF-IDF</b> retrieves relevant resources</span>
              <span style="font-size:12px;color:#94a3b8;"><b style="color:#e2e8f0;">Linear Regression</b> ranks by similarity, title, topic, phrase, and level features</span>
              <span style="font-size:12px;color:#818cf8;background:rgba(99,102,241,0.16);padding:2px 8px;border-radius:6px;font-weight:600;">{level_note}</span>
            </div>""", unsafe_allow_html=True)

            # Header + export
            c_h1, c_h2 = st.columns([3,1])
            with c_h1:
                st.markdown(f"""<div style="display:flex;align-items:center;margin:16px 0 12px;gap:12px;">
                  <h2 style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:700;color:white;margin:0;">
                    Recommended Resources</h2>
                  <span style="color:#64748b;font-size:13px;">{len(results)} for "{last_q}"</span>
                </div>""", unsafe_allow_html=True)
            with c_h2:
                csv_str = export_csv(last_q, level, top_n)
                if csv_str:
                    st.download_button("⬇ Export CSV", data=csv_str,
                        file_name=f"results_{last_q[:20].replace(' ','_')}.csv",
                        mime="text/csv", use_container_width=True)

            # Level filter pills
            all_lvls = ["All"] + sorted({r["level"] for r in results})
            sel = st.radio("", all_lvls, horizontal=True, key="lvl_filter")
            shown = results if sel=="All" else [r for r in results if r["level"]==sel]

            # Cards
            for i in range(0, len(shown), 2):
                cols = st.columns(2, gap="medium")
                for j, col in enumerate(cols):
                    if i+j >= len(shown): break
                    r    = shown[i+j]
                    lvl  = r.get("level","All Levels")
                    ttl  = r.get("title","")
                    tpc  = r.get("topic","")
                    lnk  = r.get("link","#")
                    sc   = int(r.get("score",0)*100)
                    bar  = min(sc*3,100)
                    tsc  = int(r.get("tfidf_score",0)*100)
                    rank_score = round(r.get("rank_score", r.get("gb_score",0)),4)
                    rtp  = (r.get("type","Course") or "Course").title()
                    lcfg = LEVEL_CFG.get(lvl, LEVEL_CFG["All Levels"])
                    tcfg = TYPE_CFG.get(rtp, TYPE_CFG["Course"])
                    lc, tc, icon = lcfg["color"], tcfg["color"], tcfg["icon"]

                    card_html = (
                        f'<div class="resource-card" style="background:linear-gradient(145deg,#111827,#0f172a);'
                        f'border:1px solid rgba(99,102,241,0.18);border-radius:20px;padding:22px;margin-bottom:8px;'
                        f'transition:all 0.25s ease;animation:fadeUp 0.4s ease {(i+j)*0.06}s both;">'
                        f'<div style="width:48px;height:48px;background:linear-gradient(135deg,{tc}22,{tc}11);'
                        f'border:1px solid {tc}33;border-radius:14px;display:flex;align-items:center;'
                        f'justify-content:center;font-size:22px;margin-bottom:12px;">{icon}</div>'
                        f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">'
                        f'<span style="background:{lc}18;color:{lc};border:1px solid {lc}44;'
                        f'border-radius:20px;padding:3px 10px;font-size:11px;font-weight:600;">{lvl}</span>'
                        f'<span style="background:{tc}18;color:{tc};border:1px solid {tc}44;'
                        f'border-radius:20px;padding:3px 10px;font-size:11px;font-weight:600;">{rtp}</span>'
                        f'</div>'
                        f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:15px;font-weight:700;'
                        f'color:white;line-height:1.4;margin-bottom:6px;">{ttl[:55]}{"..." if len(ttl)>55 else ""}</div>'
                        f'<div style="font-size:12px;color:#475569;margin-bottom:10px;">{tpc[:60] if tpc else ""}</div>'
                        f'<div style="margin-bottom:12px;">'
                        f'<div style="background:rgba(255,255,255,0.05);border-radius:4px;height:4px;overflow:hidden;">'
                        f'<div style="width:{bar}%;height:100%;background:linear-gradient(90deg,{lc},{lc}88);border-radius:4px;"></div>'
                        f'</div>'
                        f'<div style="display:flex;justify-content:space-between;margin-top:4px;">'
                        f'<span style="font-size:10px;color:#475569;">TF-IDF {tsc}% · Regression {rank_score}</span>'
                        f'<span style="font-size:11px;color:{lc};font-weight:600;">{sc}% match</span>'
                        f'</div></div>'
                        f'<div style="display:flex;gap:8px;flex-wrap:wrap;">'
                        f'<a href="{lnk}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;'
                        f'background:rgba(124,58,237,0.1);color:#a855f7;border:1px solid rgba(124,58,237,0.25);'
                        f'border-radius:10px;padding:7px 14px;font-size:13px;font-weight:600;text-decoration:none;">Open ↗</a>'
                        f'</div></div>'
                    )
                    with col:
                        st.markdown(card_html, unsafe_allow_html=True)
                        # Action buttons below card
                        b1, b2, b3 = st.columns(3)
                        with b1:
                            if st.button("🔖 Save", key=f"bm_{i}_{j}", use_container_width=True):
                                add_bookmark(r); st.toast(f"Saved: {ttl[:30]}...", icon="🔖")
                        with b2:
                            if st.button("⚖️ Compare", key=f"cmp_{i}_{j}", use_container_width=True):
                                if r not in st.session_state.compare_list and len(st.session_state.compare_list)<2:
                                    st.session_state.compare_list.append(r)
                                    st.toast("Added to compare", icon="⚖️")
                        with b3:
                            if st.button("🔗 Similar", key=f"sim_{i}_{j}", use_container_width=True):
                                st.session_state["_similar"] = r
                                st.session_state["_similar_results"] = fetch_similar(ttl)

            # Similar panel
            if "_similar" in st.session_state and st.session_state.get("_similar_results"):
                sim_r  = st.session_state["_similar"]
                sim_rs = st.session_state["_similar_results"]
                st.markdown(f"""<div style="margin-top:20px;padding:20px;background:#111827;
                  border:1px solid rgba(99,102,241,0.2);border-radius:16px;">
                  <div style="font-size:13px;color:#a78bfa;font-weight:600;margin-bottom:12px;">
                    🔗 Similar to: {sim_r['title'][:50]}</div>""", unsafe_allow_html=True)
                sim_cols = st.columns(min(len(sim_rs),4))
                for si, sr in enumerate(sim_rs[:4]):
                    with sim_cols[si]:
                        slvl = sr.get("level","All Levels")
                        slc  = LEVEL_CFG.get(slvl,LEVEL_CFG["All Levels"])["color"]
                        st.markdown(f"""<div style="background:#0f172a;border:1px solid rgba(99,102,241,0.15);
                          border-radius:12px;padding:14px;">
                          <span style="font-size:11px;color:{slc};font-weight:600;">{slvl}</span>
                          <div style="font-size:13px;color:white;font-weight:600;margin:6px 0;">{sr['title'][:45]}</div>
                          <div style="font-size:11px;color:#475569;">{int(sr.get('score',0)*100)}% match</div>
                          <a href="{sr['link']}" target="_blank" style="font-size:12px;color:#a855f7;text-decoration:none;">Open ↗</a>
                          </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Bottom stats
            stats_d = fetch_stats()
            by_lvl  = stats_d.get("by_level",{})
            _stat_font = "Space Grotesk"
            _stat_cards = []
            for c, ic, v, lb in [
                ("124,58,237", "📦", f"{stats_d.get('total',41322):,}+", "Total Resources"),
                ("6,182,212", "📶", len(by_lvl), "Difficulty Levels"),
                ("168,85,247", "🏷", len(stats_d.get('by_type',{})), "Resource Types"),
                ("16,185,129", "🔥", len(st.session_state.history), "Your Searches"),
            ]:
                _stat_cards.append(
                    '<div style="background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px 20px;display:flex;align-items:center;gap:14px;">'
                    f'<div style="width:44px;height:44px;background:rgba({c},0.15);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px;">{ic}</div>'
                    f'<div><div style="font-family:\'{_stat_font}\',sans-serif;font-size:20px;font-weight:800;color:white;">{v}</div>'
                    f'<div style="font-size:11px;color:#64748b;font-weight:500;margin-top:2px;">{lb}</div></div></div>'
                )
            stats_html = ''.join(_stat_cards)
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:24px;">
              {stats_html}
            </div>""", unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="text-align:center;padding:60px 0;">
              <div style="font-size:56px;margin-bottom:16px;animation:float 3s ease-in-out infinite;">🎓</div>
              <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;
                color:white;margin-bottom:8px;">Find Your Perfect Study Resources</div>
              <div style="color:#64748b;font-size:14px;">Search any topic above or click a trending topic from the sidebar</div>
            </div>""", unsafe_allow_html=True)

    # Right panel
    with right_col:
        results = st.session_state.results
        avg_sc  = int(sum(r.get("score",0) for r in results)/len(results)*100) if results else 0
        stroke  = int(avg_sc*2.83)
        gc      = "#10b981" if avg_sc>=80 else "#f59e0b" if avg_sc>=60 else "#ef4444"
        conf_pct = int(st.session_state.confidence*100)

        st.markdown(f"""
        <div style="background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px;margin-bottom:16px;text-align:center;">
          <div style="font-size:11px;font-weight:600;color:#64748b;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px;">Match Analysis</div>
          <div style="position:relative;display:inline-block;width:110px;height:110px;margin-bottom:8px;">
            <svg width="110" height="110" viewBox="0 0 120 120" style="transform:rotate(-90deg);">
              <circle cx="60" cy="60" r="45" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10"/>
              <circle cx="60" cy="60" r="45" fill="none" stroke="url(#grad)" stroke-width="10" stroke-linecap="round" stroke-dasharray="{stroke} 283"/>
              <defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:#7c3aed"/><stop offset="100%" style="stop-color:#06b6d4"/></linearGradient></defs>
            </svg>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);">
              <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:white;line-height:1;">{avg_sc}%</div>
              <div style="font-size:10px;color:#64748b;margin-top:2px;">avg match</div>
            </div>
          </div>
          {f'<div style="font-size:11px;color:#94a3b8;margin-top:4px;">RF Confidence: <b style="color:#a78bfa;">{conf_pct}%</b></div>' if conf_pct > 0 else ""}
        </div>""", unsafe_allow_html=True)

        # Resource distribution donut
        stats_d = fetch_stats(); by_lvl = stats_d.get("by_level",{})
        total_r = max(sum(by_lvl.values()),1)
        lvl_list  = list(by_lvl.items())[:4]
        lv_colors = ["#7c3aed","#06b6d4","#a855f7","#f59e0b"]
        donut_segs = ""; offset = 25
        for idx,(lv,cnt) in enumerate(lvl_list):
            pct = cnt/total_r*100; dash = pct*2.83; col2 = lv_colors[idx%4]
            donut_segs += f'<circle cx="60" cy="60" r="45" fill="none" stroke="{col2}" stroke-width="12" stroke-dasharray="{dash:.1f} {283-dash:.1f}" stroke-dashoffset="-{offset:.1f}"/>'
            offset += dash
        leg = "".join([f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;"><div style="display:flex;align-items:center;gap:7px;"><div style="width:8px;height:8px;border-radius:50%;background:{lv_colors[i%4]};"></div><span style="font-size:12px;color:#94a3b8;">{lv}</span></div><span style="font-size:12px;font-weight:600;color:white;">{int(cnt/total_r*100)}%</span></div>' for i,(lv,cnt) in enumerate(lvl_list)])
        st.markdown(f"""
        <div style="background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px;margin-bottom:16px;">
          <div style="font-size:11px;font-weight:600;color:#64748b;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px;">Dataset Distribution</div>
          <div style="display:flex;justify-content:center;margin-bottom:14px;">
            <svg width="100" height="100" viewBox="0 0 120 120" style="transform:rotate(-90deg);">
              <circle cx="60" cy="60" r="45" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="12"/>
              {donut_segs}
            </svg>
          </div>{leg}</div>""", unsafe_allow_html=True)

        # Compare quick panel
        if st.session_state.compare_list:
            st.markdown(f"""<div style="background:var(--card);border:1px solid rgba(245,158,11,0.3);
              border-radius:16px;padding:16px;margin-bottom:16px;">
              <div style="font-size:11px;font-weight:600;color:#f59e0b;letter-spacing:1px;margin-bottom:10px;">
                ⚖️ COMPARE QUEUE ({len(st.session_state.compare_list)}/2)</div>""", unsafe_allow_html=True)
            for ci, cc in enumerate(st.session_state.compare_list):
                st.markdown(f'<div style="font-size:12px;color:#94a3b8;padding:4px 0;">{ci+1}. {cc["title"][:35]}</div>', unsafe_allow_html=True)
            if len(st.session_state.compare_list)==2:
                if st.button("⚖️ Compare Now →", use_container_width=True):
                    set_page("compare"); st.rerun()
            if st.button("Clear Queue", key="clr_cmp", use_container_width=True):
                st.session_state.compare_list = []; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # Recent searches
        history = st.session_state.history
        searches_html = "".join([
            f'<div style="display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid rgba(99,102,241,0.08);">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="width:26px;height:26px;background:rgba(124,58,237,0.12);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;">🔍</div>'
            f'<span style="font-size:12px;font-weight:500;color:#e2e8f0;">{h["query"][:18]}</span></div>'
            f'<span style="font-size:11px;color:#475569;">{h.get("time","—")}</span></div>'
            for h in history[:4]
        ]) if history else '<div style="color:#475569;font-size:12px;padding:10px 0;">No searches yet</div>'
        st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px;">
          <div style="font-size:11px;font-weight:600;color:#64748b;letter-spacing:1px;text-transform:uppercase;margin-bottom:12px;">Recent Searches</div>
          {searches_html}</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: BOOKMARKS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "bookmarks":
    st.markdown("""<h2 style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:white;margin-bottom:4px;">My Bookmarks</h2>
    <p style="color:#64748b;font-size:14px;margin-bottom:24px;">Saved courses for this session</p>""", unsafe_allow_html=True)
    bms = st.session_state.bookmarks
    if not bms:
        st.markdown("""<div style="text-align:center;padding:60px 0;">
          <div style="font-size:52px;animation:float 3s ease-in-out infinite;">🔖</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:white;margin:16px 0 8px;">No bookmarks yet</div>
          <div style="color:#64748b;font-size:14px;">Click 🔖 Save on any result card to bookmark it</div>
        </div>""", unsafe_allow_html=True)
    else:
        bc1,bc2 = st.columns([4,1])
        with bc2:
            if st.button("🗑 Clear All", use_container_width=True):
                st.session_state.bookmarks = []; st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        for bi, bm in enumerate(bms):
            lvl = bm.get("level","All Levels"); lc = LEVEL_CFG.get(lvl,LEVEL_CFG["All Levels"])["color"]
            sc  = int(bm.get("score",0)*100)
            bc_1, bc_2 = st.columns([5,1])
            with bc_1:
                st.markdown(f"""<div style="background:#111827;border:1px solid rgba(99,102,241,0.18);
                  border-radius:16px;padding:18px 22px;margin-bottom:10px;">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                    <span style="background:{lc}18;color:{lc};border:1px solid {lc}44;border-radius:20px;padding:3px 10px;font-size:11px;font-weight:600;">{lvl}</span>
                    <span style="font-size:11px;color:#64748b;">{sc}% match</span>
                  </div>
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;color:white;margin-bottom:4px;">{bm['title']}</div>
                  <div style="font-size:12px;color:#475569;margin-bottom:10px;">{bm.get('topic','')[:60]}</div>
                  <a href="{bm.get('link','#')}" target="_blank" style="font-size:13px;color:#a855f7;text-decoration:none;font-weight:600;">Open course ↗</a>
                </div>""", unsafe_allow_html=True)
            with bc_2:
                if st.button("🗑", key=f"rm_bm_{bi}", use_container_width=True):
                    st.session_state.bookmarks = [b for b in bms if b["title"]!=bm["title"]]; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: COMPARE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "compare":
    st.markdown("""<h2 style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:white;margin-bottom:4px;">Compare Courses</h2>
    <p style="color:#64748b;font-size:14px;margin-bottom:24px;">Side-by-side comparison of two courses</p>""", unsafe_allow_html=True)
    cl = st.session_state.compare_list
    if len(cl) < 2:
        st.info("Add 2 courses to compare using the ⚖️ Compare button on result cards.")
        if st.button("← Go to Search"): set_page("search"); st.rerun()
    else:
        c1, c2 = cl[0], cl[1]
        LCOLS = {"Beginner":"#10b981","Introductory":"#06b6d4","Intermediate":"#3b82f6",
                 "Advanced":"#8b5cf6","Expert":"#f59e0b","All Levels":"#64748b"}
        col1, div, col2 = st.columns([2,0.1,2])
        for col, c in [(col1,c1),(col2,c2)]:
            with col:
                lv = c.get("level","All Levels"); lc = LCOLS.get(lv,"#64748b")
                sc = int(c.get("score",0)*100)
                st.markdown(f"""<div style="background:#111827;border:1px solid rgba(99,102,241,0.2);
                  border-radius:20px;padding:28px;min-height:340px;">
                  <span style="background:{lc}18;color:{lc};border:1px solid {lc}44;border-radius:20px;
                    padding:4px 12px;font-size:12px;font-weight:600;">{lv}</span>
                  <h3 style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:800;
                    color:white;margin:16px 0 8px;">{c['title']}</h3>
                  <p style="font-size:13px;color:#64748b;margin-bottom:16px;">{c.get('topic','')[:80]}</p>
                  <table style="width:100%;font-size:13px;border-collapse:collapse;">
                    <tr><td style="padding:6px 0;color:#94a3b8;">Match Score</td>
                        <td style="color:{lc};font-weight:700;text-align:right;">{sc}%</td></tr>
                    <tr><td style="padding:6px 0;color:#94a3b8;border-top:1px solid rgba(99,102,241,0.1);">TF-IDF</td>
                        <td style="color:white;text-align:right;border-top:1px solid rgba(99,102,241,0.1);">{int(c.get('tfidf_score',0)*100)}%</td></tr>
                    <tr><td style="padding:6px 0;color:#94a3b8;border-top:1px solid rgba(99,102,241,0.1);">Level</td>
                        <td style="color:white;text-align:right;border-top:1px solid rgba(99,102,241,0.1);">{lv}</td></tr>
                    <tr><td style="padding:6px 0;color:#94a3b8;border-top:1px solid rgba(99,102,241,0.1);">Type</td>
                        <td style="color:white;text-align:right;border-top:1px solid rgba(99,102,241,0.1);">{c.get('type','Course')}</td></tr>
                  </table>
                  <div style="margin-top:16px;">
                    <div style="background:rgba(255,255,255,0.05);border-radius:4px;height:6px;overflow:hidden;">
                      <div style="width:{min(sc*3,100)}%;height:100%;background:linear-gradient(90deg,{lc},{lc}88);border-radius:4px;"></div>
                    </div>
                  </div>
                  <a href="{c.get('link','#')}" target="_blank" style="display:inline-block;margin-top:16px;
                    background:rgba(124,58,237,0.1);color:#a855f7;border:1px solid rgba(124,58,237,0.25);
                    border-radius:10px;padding:8px 16px;font-size:13px;font-weight:600;text-decoration:none;">Open ↗</a>
                </div>""", unsafe_allow_html=True)
        # Winner
        if c1.get("score",0) != c2.get("score",0):
            winner = c1 if c1.get("score",0) > c2.get("score",0) else c2
            st.markdown(f"""<div style="text-align:center;margin-top:20px;padding:16px;
              background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);border-radius:12px;">
              <span style="color:#10b981;font-weight:700;">🏆 Better Match: {winner['title'][:50]}</span>
              <span style="color:#64748b;font-size:13px;"> — {int(winner.get('score',0)*100)}% match score</span>
            </div>""", unsafe_allow_html=True)
        if st.button("Clear & Compare New", use_container_width=True):
            st.session_state.compare_list = []; set_page("search"); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "analytics":
    st.markdown("""<h2 style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:white;margin-bottom:4px;">Analytics Dashboard</h2>
    <p style="color:#64748b;font-size:14px;margin-bottom:24px;">Dataset insights, session stats, and search logs</p>""", unsafe_allow_html=True)
    stats = fetch_stats()
    if not stats:
        st.warning("Start the Flask backend: `python app.py`")
    else:
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Total Resources", f"{stats.get('total',0):,}")
        k2.metric("Difficulty Levels", len(stats.get("by_level",{})))
        k3.metric("Resource Types", len(stats.get("by_type",{})))
        k4.metric("Session Searches", len(st.session_state.history))

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        LCOLS = {"Beginner":"#10b981","Intermediate":"#3b82f6","Advanced":"#8b5cf6",
                 "Expert":"#f59e0b","All Levels":"#64748b","Introductory":"#06b6d4"}
        with c1:
            st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:16px;font-weight:700;color:white;margin-bottom:14px;">Distribution by Level</div>', unsafe_allow_html=True)
            total_r = sum(stats.get("by_level",{}).values()) or 1
            for lv,cnt in sorted(stats.get("by_level",{}).items(),key=lambda x:-x[1]):
                pct = int(cnt/total_r*100); c3 = LCOLS.get(lv,"#64748b")
                st.markdown(f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:13px;color:#94a3b8;">{lv}</span><span style="font-size:13px;color:white;font-weight:600;">{cnt:,} · {pct}%</span></div>'
                    f'<div style="background:rgba(255,255,255,0.05);border-radius:6px;height:7px;margin-bottom:11px;overflow:hidden;">'
                    f'<div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{c3},{c3}88);border-radius:6px;"></div></div>',
                    unsafe_allow_html=True)
        with c2:
            st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:16px;font-weight:700;color:white;margin-bottom:14px;">Sample Topics</div>', unsafe_allow_html=True)
            chips = "".join([f'<span style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.2);border-radius:8px;padding:5px 12px;margin:3px;display:inline-block;font-size:12px;color:#a78bfa;font-weight:500;">{t[:22]}</span>' for t in stats.get("sample_topics",[])[:16]])
            st.markdown(f'<div style="line-height:2.6;">{chips}</div>', unsafe_allow_html=True)

        # Session summary
        if st.session_state.history:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:16px;font-weight:700;color:white;margin-bottom:14px;">Session Overview</div>', unsafe_allow_html=True)
            s1,s2,s3,s4 = st.columns(4)
            s1.metric("Searches", len(st.session_state.history))
            s2.metric("Total Results", sum(h["count"] for h in st.session_state.history))
            s3.metric("Unique Topics", len({h["query"] for h in st.session_state.history}))
            s4.metric("Bookmarks", len(st.session_state.bookmarks))

        # Trending
        trending = fetch_trending()
        if trending:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:16px;font-weight:700;color:white;margin-bottom:14px;">🔥 All-Time Trending Searches</div>', unsafe_allow_html=True)
            max_cnt = max(t["count"] for t in trending) or 1
            for t in trending:
                pct = int(t["count"]/max_cnt*100)
                st.markdown(f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:13px;color:#94a3b8;">{t["query"]}</span><span style="font-size:13px;color:white;font-weight:600;">{t["count"]}×</span></div>'
                    f'<div style="background:rgba(255,255,255,0.05);border-radius:6px;height:6px;margin-bottom:10px;overflow:hidden;">'
                    f'<div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#f59e0b,#f59e0b88);border-radius:6px;"></div></div>',
                    unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: ML MODELS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "models":
    st.markdown("""<h2 style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:white;margin-bottom:4px;">ML Models Dashboard</h2>
    <p style="color:#64748b;font-size:14px;margin-bottom:24px;">Training metrics, performance, and model details</p>""", unsafe_allow_html=True)
    details = fetch_model_details()
    rf = details.get("random_forest",{})
    gb = details.get("gradient_boosting",{})
    lr = details.get("linear_regression",{})

    if not rf and not gb and not lr:
        st.warning("Backend offline or models not yet trained. Run: `python app.py`")
    else:
        # Model cards
        m1, m2, m3 = st.columns(3)
        with m1:
            acc = rf.get("accuracy",0)
            acc_color = "#10b981" if acc>=0.9 else "#f59e0b" if acc>=0.75 else "#ef4444"
            st.markdown(f"""<div style="background:#111827;border:1px solid rgba(99,102,241,0.2);border-radius:20px;padding:28px;min-height:260px;">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
                <div style="width:48px;height:48px;background:rgba(124,58,237,0.2);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:22px;">🌲</div>
                <div><div style="font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:700;color:white;">Random Forest</div>
                <div style="font-size:12px;color:#64748b;">Diagnostic Level Classifier</div></div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">
                <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;text-align:center;">
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:{acc_color};">{acc:.1%}</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;">Test Accuracy</div>
                </div>
                <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;text-align:center;">
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:#a855f7;">200</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;">Estimators</div>
                </div>
              </div>
              <div style="font-size:12px;color:#64748b;">Predicts: {", ".join(rf.get("classes",[])[:4])}{" ..." if len(rf.get("classes",[]))>4 else ""}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            rmse = gb.get("rmse",0); r2 = gb.get("r2",0)
            r2_color = "#10b981" if r2>=0.9 else "#f59e0b" if r2>=0.7 else "#ef4444"
            st.markdown(f"""<div style="background:#111827;border:1px solid rgba(99,102,241,0.2);border-radius:20px;padding:28px;min-height:260px;">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
                <div style="width:48px;height:48px;background:rgba(6,182,212,0.2);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:22px;">📈</div>
                <div><div style="font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:700;color:white;">Gradient Boosting</div>
                <div style="font-size:12px;color:#64748b;">Diagnostic Regressor</div></div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">
                <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;text-align:center;">
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:{r2_color};">{r2:.3f}</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;">R² Score</div>
                </div>
                <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;text-align:center;">
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:#06b6d4;">{rmse:.6f}</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;">RMSE</div>
                </div>
              </div>
              <div style="font-size:12px;color:#64748b;">Kept for model comparison; live ranking uses Linear Regression</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            features = lr.get("features",[])
            coefs = lr.get("coefficients",[])
            top_features = ", ".join([f"{name.replace('_',' ')} {coef:.2f}" for name, coef in list(zip(features, coefs))[:3]]) if features and coefs else "Similarity and match features"
            st.markdown(f"""<div style="background:#111827;border:1px solid rgba(99,102,241,0.2);border-radius:20px;padding:28px;min-height:260px;">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
                <div style="width:48px;height:48px;background:rgba(16,185,129,0.2);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:22px;">LR</div>
                <div><div style="font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:700;color:white;">Linear Regression</div>
                <div style="font-size:12px;color:#64748b;">Live Relevance Ranker</div></div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">
                <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;text-align:center;">
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:#10b981;">{len(features) or 5}</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;">Features</div>
                </div>
                <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;text-align:center;">
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:#a855f7;">Live</div>
                  <div style="font-size:11px;color:#64748b;margin-top:4px;">Used Now</div>
                </div>
              </div>
              <div style="font-size:12px;color:#64748b;">Scores candidates with: {top_features}</div>
            </div>""", unsafe_allow_html=True)

        # Confusion matrix heatmap (RF)
        cm = rf.get("confusion_matrix",[])
        classes = rf.get("classes",[])
        if cm and classes:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:16px;font-weight:700;color:white;margin-bottom:14px;">🔥 Confusion Matrix — Random Forest</div>', unsafe_allow_html=True)
            max_val = max(max(row) for row in cm) or 1
            n = len(classes)
            header = "<tr><td style='padding:6px;'></td>" + "".join([f"<td style='padding:6px;font-size:11px;color:#64748b;text-align:center;font-weight:600;'>{c[:10]}</td>" for c in classes]) + "</tr>"
            rows_html = ""
            for ri, row in enumerate(cm):
                rows_html += f"<tr><td style='padding:6px;font-size:11px;color:#94a3b8;font-weight:600;white-space:nowrap;'>{classes[ri][:10]}</td>"
                for ci, v in enumerate(row):
                    alpha = max(0.12, v/max_val*0.9)
                    bg = f"rgba(124,58,237,{alpha:.2f})" if ri==ci else f"rgba(239,68,68,{alpha:.2f})" if v>0 else "rgba(255,255,255,0.03)"
                    rows_html += f"<td style='padding:8px;text-align:center;background:{bg};border-radius:6px;font-size:13px;font-weight:600;color:white;'>{v}</td>"
                rows_html += "</tr>"
            st.markdown(f'<div style="overflow-x:auto;"><table style="border-collapse:separate;border-spacing:3px;">{header}{rows_html}</table></div>', unsafe_allow_html=True)

        # GB feature importance
        fi = gb.get("feature_importance",[])
        if fi:
            feat_names = ["TF-IDF Score","Level Num","Title Length","Topic Length","Interaction"]
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:16px;font-weight:700;color:white;margin-bottom:14px;">📊 Feature Importance — Gradient Boosting</div>', unsafe_allow_html=True)
            max_fi = max(fi) or 1
            for fn, fv in sorted(zip(feat_names,fi), key=lambda x:-x[1]):
                pct = fv/max_fi*100
                st.markdown(f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:13px;color:#94a3b8;">{fn}</span><span style="font-size:13px;color:white;font-weight:600;">{fv:.4f}</span></div>'
                    f'<div style="background:rgba(255,255,255,0.05);border-radius:6px;height:7px;margin-bottom:11px;overflow:hidden;">'
                    f'<div style="width:{pct:.1f}%;height:100%;background:linear-gradient(90deg,#06b6d4,#06b6d488);border-radius:6px;"></div></div>',
                    unsafe_allow_html=True)

        # Pipeline diagram
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:16px;font-weight:700;color:white;margin-bottom:14px;">🔄 ML Pipeline Flow</div>', unsafe_allow_html=True)
        steps = [("1. Query Input","User types topic"),("2. TF-IDF","Vectorize query"),
                 ("3. Cosine Similarity","Find candidates"),("4. Linear Regression","Score & rank"),("5. Results","Top-N output")]
        cols_p = st.columns(len(steps))
        for pi,(step,desc) in enumerate(steps):
            with cols_p[pi]:
                arrow = "→" if pi < len(steps)-1 else "✅"
                st.markdown(f"""<div style="background:#111827;border:1px solid rgba(99,102,241,0.2);
                  border-radius:12px;padding:14px;text-align:center;min-height:80px;">
                  <div style="font-size:11px;color:#a78bfa;font-weight:700;margin-bottom:4px;">{step}</div>
                  <div style="font-size:11px;color:#64748b;">{desc}</div>
                </div>
                <div style="text-align:center;color:#475569;font-size:18px;margin-top:4px;">{arrow if pi<len(steps)-1 else ""}</div>""", unsafe_allow_html=True)

        # Retrain button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Retrain Both Models", use_container_width=False):
            with st.spinner("Retraining models — this may take a minute..."):
                try:
                    r = requests.post(f"{API_BASE}/retrain", timeout=300)
                    if r.ok:
                        d = r.json()
                        st.success(f"✅ Models retrained! RF Accuracy: {d.get('rf_accuracy',0):.1%} | GB RMSE: {d.get('gb_rmse',0):.6f} | Live ranker: Linear Regression")
                        st.cache_data.clear()
                    else: st.error("Retrain failed.")
                except Exception as e: st.error(str(e))

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "history":
    st.markdown("""<h2 style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:white;margin-bottom:4px;">Search History</h2>
    <p style="color:#64748b;font-size:14px;margin-bottom:24px;">Your previous searches this session</p>""", unsafe_allow_html=True)
    history = st.session_state.history
    if not history:
        st.markdown("""<div style="text-align:center;padding:80px 0;">
          <div style="font-size:52px;animation:float 3s ease-in-out infinite;">🕐</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:white;margin:16px 0 8px;">No history yet</div>
          <div style="color:#64748b;font-size:14px;">Start searching to see history here</div>
        </div>""", unsafe_allow_html=True)
    else:
        if st.button("🗑 Clear All History"):
            st.session_state.history = []; st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        LCOLS2 = {"Beginner":"#10b981","Intermediate":"#3b82f6","Advanced":"#8b5cf6",
                  "Expert":"#f59e0b","All Levels":"#64748b","Introductory":"#06b6d4"}
        for i, h in enumerate(history):
            lc = LCOLS2.get(h.get("level","All Levels"),"#64748b")
            pl = h.get("predicted_level","")
            with st.expander(f"🔍 {h['query']}  ·  {h['count']} results  ·  {h.get('time','')}", expanded=(i==0)):
                ca, cb = st.columns([3,1])
                with ca:
                    tags = f'<span style="background:rgba(124,58,237,0.1);color:#a855f7;border:1px solid rgba(124,58,237,0.2);border-radius:8px;padding:4px 12px;font-size:13px;font-weight:600;">{h["query"]}</span>'
                    tags += f' <span style="background:{lc}18;color:{lc};border:1px solid {lc}33;border-radius:8px;padding:4px 12px;font-size:13px;font-weight:600;">{h.get("level","All Levels")}</span>'
                    tags += f' <span style="background:rgba(16,185,129,0.1);color:#10b981;border:1px solid rgba(16,185,129,0.2);border-radius:8px;padding:4px 12px;font-size:13px;font-weight:600;">{h["count"]} results</span>'
                    if pl and pl not in ("All", "All Levels"):
                        tags += f' <span style="background:rgba(99,102,241,0.1);color:#818cf8;border:1px solid rgba(99,102,241,0.2);border-radius:8px;padding:4px 12px;font-size:12px;">Level filter: {pl}</span>'
                    st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;">{tags}</div>', unsafe_allow_html=True)
                with cb:
                    if st.button("Re-run →", key=f"rr_{i}"):
                        st.session_state["_quick"] = h["query"]; set_page("search"); st.rerun()
                for r in h["results"][:3]:
                    lvl=r.get("level","All Levels"); lcfg=LEVEL_CFG.get(lvl,LEVEL_CFG["All Levels"]); sc2=int(r.get("score",0)*100)
                    st.markdown(f'<div style="background:rgba(17,24,39,0.6);border:1px solid rgba(99,102,241,0.12);border-radius:12px;padding:12px 16px;margin-bottom:6px;">'
                        f'<div style="display:flex;gap:6px;margin-bottom:6px;">'
                        f'<span style="background:{lcfg["bg"]};color:{lcfg["color"]};border:1px solid {lcfg["border"]};border-radius:20px;padding:2px 9px;font-size:11px;font-weight:600;">{lvl}</span>'
                        f'<span style="margin-left:auto;color:{lcfg["color"]};font-size:11px;font-weight:700;">{sc2}% match</span></div>'
                        f'<div style="font-size:13px;font-weight:600;color:white;">{r.get("title","")[:55]}</div></div>', unsafe_allow_html=True)
                if len(h["results"])>3:
                    st.caption(f"+ {len(h['results'])-3} more. Re-run to view all.")

st.markdown('</div>', unsafe_allow_html=True)
