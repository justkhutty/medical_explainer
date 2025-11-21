# medical_explainer.py
import streamlit as st
import openai
import difflib
import time
import json

# ---------------------------
# Basic page config + styles
# ---------------------------
st.set_page_config(page_title="Medical Terminology Explainer", layout="wide")
# Light/Dark toggle
if "theme_dark" not in st.session_state:
    st.session_state.theme_dark = False

def inject_css():
    dark = st.session_state.theme_dark
    bg = "#0f1724" if dark else "#f7fafc"
    card_bg = "#0b1220" if dark else "#ffffff"
    text = "#e6eef8" if dark else "#0b1220"
    accent = "#3b82f6"
    st.markdown(
        f"""
        <style>
        :root {{
            --bg: {bg};
            --card: {card_bg};
            --text: {text};
            --accent: {accent};
        }}
        .reportview-container, .main {{
            background: var(--bg);
            color: var(--text);
        }}
        /* Floating search */
        .floating-search {{
            position: fixed;
            top: 12px;
            left: 50%;
            transform: translateX(-50%);
            width: min(880px, 92%);
            z-index: 9999;
        }}
        .material-card {{
            background: var(--card);
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 6px 18px rgba(16,24,40,0.08);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            margin-bottom: 18px;
        }}
        .material-card:hover {{
            transform: translateY(-6px);
            box-shadow: 0 20px 40px rgba(16,24,40,0.12);
        }}
        .term-title {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .chips {{
            display:flex;
            gap:8px;
            flex-wrap:wrap;
            margin-top:8px;
        }}
        .chip {{
            background: var(--accent);
            color: white;
            padding:6px 10px;
            border-radius:999px;
            font-weight:600;
            font-size:13px;
        }}
        .icon {{
            font-size:20px;
            margin-right:8px;
        }}
        details summary {{
            cursor: pointer;
            font-weight:600;
            margin-bottom:6px;
        }}
        /* smooth fade */
        .fade-in {{
            animation: fadeIn 0.35s ease-in-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()

# ---------------------------
# Check API Key (no prompt)
# ---------------------------
if "OPENAI_API_KEY" not in st.secrets:
    st.error("API key missing. Add OPENAI_API_KEY to .streamlit/secrets.toml")
    st.stop()
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ---------------------------
# Small local term dataset (starter)
# ---------------------------
# You can expand this list or load from a file/db
LOCAL_TERMS = {
    "myocardial infarction": {"system": "Cardiovascular", "icon": "🫀"},
    "stroke": {"system": "Neurology", "icon": "🧠"},
    "appendicitis": {"system": "Gastrointestinal", "icon": "🍽️"},
    "deep vein thrombosis": {"system": "Cardiovascular", "icon": "🫀"},
    "pulmonary embolism": {"system": "Respiratory", "icon": "🫁"},
    "fracture": {"system": "Musculoskeletal", "icon": "🦴"},
    "sprain": {"system": "Musculoskeletal", "icon": "🦵"},
    "hypertension": {"system": "Cardiovascular", "icon": "🫀"},
    "diabetes mellitus": {"system": "Endocrine", "icon": "🧪"},
    "pneumonia": {"system": "Respiratory", "icon": "🫁"},
    "anaphylaxis": {"system": "Allergy/Immunology", "icon": "🩺"},
    "concussion": {"system": "Neurology", "icon": "🧠"},
    "gallstones": {"system": "Gastrointestinal", "icon": "🍽️"},
    "cholecystectomy": {"system": "Surgical", "icon": "🔪"},
}

ALL_TERMS = sorted(list(LOCAL_TERMS.keys()))

# ---------------------------
# Sidebar: Body systems + controls
# ---------------------------
with st.sidebar:
    st.header("Filters & Settings")
    body_system = st.multiselect(
        "Filter by body system",
        options=sorted({v["system"] for v in LOCAL_TERMS.values()}),
        default=[],
    )
    st.write("Theme")
    st.checkbox("Dark mode", value=st.session_state.theme_dark, key="theme_dark", on_change=inject_css)
    st.markdown("---")
    st.markdown("**Quick categories**")
    st.button("Cardiovascular", key="cv_btn")
    st.button("Neurology", key="neuro_btn")
    st.write("")
    st.markdown("---")
    st.caption("This tool provides informational definitions only — not medical advice.")

# Handle quick buttons (simple logic)
if st.session_state.get("cv_btn", False):
    body_system = ["Cardiovascular"]
if st.session_state.get("neuro_btn", False):
    body_system = ["Neurology"]

# ---------------------------
# Floating Search Bar (top)
# ---------------------------
st.markdown(
    """
    <div class="floating-search">
    </div>
    """,
    unsafe_allow_html=True,
)

# Create a centered search area visually at top
search_col1, search_col2, search_col3 = st.columns([1, 6, 1])
with search_col2:
    query = st.text_input(
        "Search medical term, condition, anatomy or procedure",
        key="term_query",
        placeholder="e.g. myocardial infarction, appendicitis, concussion...",
    )

# Auto-suggest as you type using difflib
def suggest_terms(q, n=6):
    if not q or len(q.strip()) < 1:
        return []
    q = q.lower()
    # candidate list respects the selected body_system filter
    candidates = ALL_TERMS
    if body_system:
        candidates = [t for t in candidates if LOCAL_TERMS.get(t, {}).get("system") in body_system]
    # get close matches
    suggestions = difflib.get_close_matches(q, candidates, n=n, cutoff=0.1)
    # also include prefix matches
    prefix = [t for t in candidates if t.startswith(q) and t not in suggestions]
    return (prefix + suggestions)[:n]

suggestions = suggest_terms(st.session_state.get("term_query", ""))

# Show suggestions inline
if suggestions:
    sug_html = "<div class='chips'>"
    for s in suggestions:
        sug_html += f"<span class='chip' onclick=\"window.parent.postMessage({{'type':'select','term':'{s}'}}, '*')\">{LOCAL_TERMS.get(s,{}).get('icon','')} {s.title()}</span>"
    sug_html += "</div>"
    st.markdown(sug_html, unsafe_allow_html=True)

# Small JS to allow chip clicks to set text_input (works in Streamlit)
st.components.v1.html(
    """
    <script>
    window.addEventListener('message', (e) => {
        if(e.data && e.data.type === 'select' && e.data.term){
            const term = e.data.term;
            const el = window.parent.document.querySelector('input[type="text"]');
            if(el){ el.value = term; el.dispatchEvent(new Event('input', { bubbles: true })); }
        }
    });
    </script>
    """,
    height=0,
)

# ---------------------------
# System prompt for model (non-diagnostic)
# ---------------------------
SYSTEM_PROMPT = """
You are a medical knowledge assistant that provides **concise**, factual, **non-diagnostic** explanations for medical terms, conditions, anatomy, and procedures.
Rules:
- Provide sections: Definition, Typical causes, Typical symptoms, Brief management overview (informational only), Related terms.
- NEVER give medical advice, diagnoses, therapy plans, or instructions. If the user asks for medical advice, respond with: "I can provide information about medical terms but cannot give medical advice. Please consult a licensed professional."
- If asked about prognosis or what someone should do, redirect to seeking professional care.
- When giving causes/symptoms, be concise and neutral; cite common mechanisms when relevant.
- If asked about rare or experimental treatments, state that the information may be limited.
- Keep responses structured and labeled.
"""

# ---------------------------
# Function: query the model (caching)
# ---------------------------
@st.cache_data(show_spinner=False)
def ask_model(term: str, system_prompt: str = SYSTEM_PROMPT, model="gpt-4.1-mini"):
    # Build user prompt
    user_msg = f"Provide a clear, structured entry for the medical term or phrase: '{term}'."
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=700,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error from model: {str(e)}"

# ---------------------------
# Function: get related terms (small heuristic then model)
# ---------------------------
@st.cache_data(show_spinner=False)
def get_related_terms(term: str):
    # simple heuristic: terms that share words
    related = []
    tparts = set(term.lower().split())
    for t in ALL_TERMS:
        if t == term.lower():
            continue
        if tparts & set(t.split()):
            related.append(t)
    # If few related, ask model for a short list
    if len(related) < 4:
        prompt = f"List 5 concise related medical terms for '{term}' (comma separated). Only terms, no explanations."
        try:
            resp = openai.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that only returns a short comma-separated list of medical terms."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=60,
                temperature=0.3,
            )
            text = response_text = resp.choices[0].message.content
            # parse comma separated items
            parsed = [x.strip().lower() for x in response_text.replace("\n", " ").split(",") if x.strip()]
            for p in parsed:
                if p and p not in related and p in ALL_TERMS:
                    related.append(p)
        except Exception:
            pass
    return related[:6]

# ---------------------------
# Main content area
# ---------------------------
content_col1, content_col2 = st.columns([3, 2])
with content_col1:
    st.markdown("<div class='material-card fade-in'>", unsafe_allow_html=True)
    if not query:
        st.markdown("### 🔎 Start by searching a medical term (or pick a suggestion above).", unsafe_allow_html=True)
        st.markdown("Try: **myocardial infarction**, **appendicitis**, **concussion**.", unsafe_allow_html=True)
    else:
        # If query matches a local term exactly (case-insensitive)
        q_lower = query.strip().lower()
        # Optionally enforce the body system filter
        if body_system and q_lower in LOCAL_TERMS and LOCAL_TERMS[q_lower]["system"] not in body_system:
            st.warning(f"Note: the term exists but is outside the selected body system filter.")
        # Show a small loader while calling model
        with st.spinner("Fetching definition..."):
            model_output = ask_model(q_lower)
            # Slight delay for nicer animation feel
            time.sleep(0.2)

        # Parse model output roughly - display as-is but encourage structure
        st.markdown(f"<div class='term-title'>🔬 {query.title()}</div>", unsafe_allow_html=True)
        # Icon & system
        icon = LOCAL_TERMS.get(q_lower, {}).get("icon", "🩺")
        system_name = LOCAL_TERMS.get(q_lower, {}).get("system", "General")
        st.markdown(f"<div style='display:flex;align-items:center;gap:10px'><div class='icon'>{icon}</div><div style='font-weight:600'>{system_name}</div></div>", unsafe_allow_html=True)

        # Disclaimer
        st.info("**Not medical advice.** This tool provides informational definitions only. For personal medical concerns, consult a licensed professional.")

        # Show content in expandable card-like sections if model provided headings; otherwise show raw text
        # We'll try to split by common headings or just place in one block
        lower_out = model_output.lower()
        # if the model included "definition:" etc, render in sections
        sections = {}
        known_headers = ["definition", "causes", "typical causes", "symptoms", "typical symptoms", "management", "treatment", "related terms", "related"]
        # naive split
        for hdr in known_headers:
            if hdr + ":" in lower_out:
                # find header and extract until next header
                parts = lower_out.split(hdr + ":")
                # take last occurrence
                content_after = parts[-1]
                # cut off at next known header occurrence
                next_positions = [content_after.find(k + ":") for k in known_headers if content_after.find(k + ":") != -1]
                if next_positions:
                    cut = min([p for p in next_positions if p >= 0])
                    chunk = content_after[:cut].strip()
                else:
                    chunk = content_after.strip()
                sections[hdr] = chunk

        # Render sections if detected
        if sections:
            # render definition first
            def_text = sections.get("definition", None)
            if not def_text:
                # fallback: show the first 250 chars as summary
                def_text = model_output.strip().split("\n")[0][:800]
            st.markdown(f"**Definition**\n\n{def_text}")
            if "causes" in sections:
                st.markdown(f"**Causes**\n\n{sections['causes']}")
            elif "typical causes" in sections:
                st.markdown(f"**Typical causes**\n\n{sections['typical causes']}")
            if "symptoms" in sections:
                st.markdown(f"**Typical symptoms**\n\n{sections['symptoms']}")
            elif "typical symptoms" in sections:
                st.markdown(f"**Typical symptoms**\n\n{sections['typical symptoms']}")
            if "management" in sections or "treatment" in sections:
                mg = sections.get("management", sections.get("treatment", ""))
                st.markdown(f"**Brief management overview (informational only)**\n\n{mg}")
            if "related terms" in sections or "related" in sections:
                rel = sections.get("related terms", sections.get("related", ""))
                # render as chips
                rel_list = [r.strip() for r in rel.replace("\n", ",").split(",") if r.strip()]
                if rel_list:
                    st.markdown("**Related terms**")
                    chips_html = "<div class='chips'>"
                    for r in rel_list[:8]:
                        chips_html += f"<span class='chip'>{r.title()}</span>"
                    chips_html += "</div>"
                    st.markdown(chips_html, unsafe_allow_html=True)
        else:
            # no structure found — show raw but keep it pretty
            st.markdown(model_output)

        # Also show a "Quick facts" collapsible
        with st.expander("Show structured sections"):
            st.write(model_output)

    st.markdown("</div>", unsafe_allow_html=True)

# Right-side: related terms, quick links
with content_col2:
    st.markdown("<div class='material-card fade-in'>", unsafe_allow_html=True)
    st.markdown("### 🔗 Related & Quick Links")
    if query:
        related = get_related_terms(query.strip().lower())
        if related:
            for r in related:
                st.button(r.title(), key=f"rel_{r}", on_click=lambda term=r: st.session_state.update({"term_query": term}))
        else:
            st.write("No related terms found.")
    else:
        st.markdown("**Popular terms**")
        for t in ["Myocardial Infarction", "Stroke", "Appendicitis", "Concussion"]:
            st.button(t, key=f"pop_{t}", on_click=lambda term=t.lower(): st.session_state.update({"term_query": term}))
    st.markdown("---")
    st.markdown("### 🧭 Body Systems")
    system_counts = {}
    for t, v in LOCAL_TERMS.items():
        system_counts[v["system"]] = system_counts.get(v["system"], 0) + 1
    for s, count in sorted(system_counts.items(), key=lambda x: x[0]):
        st.markdown(f"- **{s}** ({count})")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Footer: credits / version
# ---------------------------
st.markdown(
    """
    <div style='margin-top:18px;opacity:0.8'>
    <small>Built for education. Not for clinical use. © Medical Explainer • Non-diagnostic content only.</small>
    </div>
    """,
    unsafe_allow_html=True,
)
