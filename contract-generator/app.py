import re
import os
import json
import base64
import tempfile
from datetime import date
from glob import glob
 
import streamlit as st
from docxtpl import DocxTemplate
 
# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
 
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
CONTRACTS_DIR = os.path.join(BASE_DIR, "contracts")
APP_CONFIG    = os.path.join(BASE_DIR, "app_config.json")
 
WEEKDAYS_PT = {
    0: "Segunda-feira", 1: "Terca-feira", 2: "Quarta-feira",
    3: "Quinta-feira",  4: "Sexta-feira", 5: "Sabado", 6: "Domingo",
}
CPF_RE = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
 
 
# ─────────────────────────────────────────────
# CONFIG LOADERS
# ─────────────────────────────────────────────
 
@st.cache_data
def load_app_config() -> dict:
    defaults = {
        "app_name":             "Contract Generator",
        "app_subtitle":         "Document System",
        "password":             "1234",
        "logo":                 "logo.png",
        "default_theme":        "dark",
        "accent_color":         "#1d6aff",
        "accent_hover":         "#0d4fd4",
        "accent_success":       "#0ea86e",
        "accent_success_hover": "#0b8f5c",
        "dark_bg_from":         "#060d1f",
        "dark_bg_mid":          "#0b1a3a",
        "dark_bg_to":           "#071228",
        "dark_surface":         "rgba(255,255,255,0.03)",
        "dark_surface_border":  "rgba(96,165,250,0.10)",
        "dark_text_main":       "#e8f0fe",
        "dark_text_sub":        "#4a6a9a",
        "dark_text_label":      "#7bafd4",
        "dark_input_bg":        "rgba(255,255,255,0.04)",
        "dark_input_border":    "rgba(96,165,250,0.20)",
        "light_bg_from":        "#f0f4ff",
        "light_bg_mid":         "#ffffff",
        "light_bg_to":          "#f5f7ff",
        "light_surface":        "rgba(0,0,0,0.02)",
        "light_surface_border": "rgba(0,0,0,0.08)",
        "light_text_main":      "#0f1c3f",
        "light_text_sub":       "#6b7fa3",
        "light_text_label":     "#3a5a9a",
        "light_input_bg":       "#ffffff",
        "light_input_border":   "rgba(0,0,0,0.12)",
        "font_heading":         "Plus Jakarta Sans",
        "font_body":            "Inter",
        "font_google_url":      "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap",
        "border_radius_card":   "16px",
        "border_radius_input":  "10px",
        "border_radius_button": "10px",
    }
    try:
        with open(APP_CONFIG, "r", encoding="utf-8") as f:
            return {**defaults, **json.load(f)}
    except FileNotFoundError:
        return defaults
 
 
@st.cache_data
def load_contracts() -> list:
    contracts = []
    for path in sorted(glob(os.path.join(CONTRACTS_DIR, "*.json"))):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["_id"] = os.path.splitext(os.path.basename(path))[0]
        contracts.append(data)
    return contracts
 
 
# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
 
def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
 
def get_logo_b64(filename: str) -> str:
    try:
        with open(os.path.join(BASE_DIR, filename), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""
 
def resolve_template(template_filename: str, contract_id: str) -> str:
    for path in [
        os.path.join(CONTRACTS_DIR, template_filename),
        os.path.join(BASE_DIR, template_filename),
        os.path.join(CONTRACTS_DIR, f"{contract_id}.docx"),
    ]:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Template '{template_filename}' not found.")
 
def render_docx(template_path: str, context: dict) -> bytes:
    doc = DocxTemplate(template_path)
    doc.render(context)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    try:
        doc.save(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp.name)
 
def show_contract_preview(docx_bytes: bytes):
    import mammoth, io
    with st.spinner("Gerando pre-visualizacao..."):
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
    st.markdown(f"""
    <div style="background:#fff;padding:60px 80px;max-width:860px;margin:0 auto;
        font-family:'Inter',sans-serif;font-size:14px;line-height:1.8;color:#111;
        border:1px solid #e5e7eb;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.12);">
        {result.value}
    </div>""", unsafe_allow_html=True)
 
def build_filename(contract: dict, context: dict) -> str:
    parts = [
        str(context.get(k, "")).replace("/", "-").replace(" ", "_")
        for k in contract.get("filename_fields", [])
    ]
    slug = "_".join(p for p in parts if p)
    return f"contrato_{slug or contract.get('_id', 'contrato')}.docx"
 
 
# ─────────────────────────────────────────────
# FIELD RENDERER
# ─────────────────────────────────────────────
 
def render_field(field: dict, form_key: str, saved: dict = None):
    ftype  = field.get("type", "text")
    if ftype == "derived":
        return None
    key    = field["key"]
    label  = field.get("label", key)
    req    = field.get("required", False)
    ph     = field.get("placeholder", "")
    wkey   = f"{form_key}_{key}"
    dlabel = f"{label} *" if req else label
    sv     = (saved or {}).get(key)
 
    if ftype in ("text", "cpf"):
        return st.text_input(dlabel, value=sv or "", placeholder=ph, key=wkey)
    if ftype == "textarea":
        return st.text_area(dlabel, value=sv or "", placeholder=ph, height=90, key=wkey)
    if ftype == "number":
        return st.number_input(dlabel, min_value=0, value=int(sv) if sv else None,
                               step=1, placeholder=ph, key=wkey)
    if ftype == "currency":
        return st.number_input(dlabel, min_value=0.0, value=float(sv) if sv else None,
                               step=50.0, format="%.2f", placeholder=ph, key=wkey)
    if ftype == "date":
        past   = field.get("past_only", False)
        future = field.get("future_only", False)
        mn  = date(1920,1,1) if past else (date.today() if future else date(1920,1,1))
        mx  = date.today() if past else None
        kw  = {"value": sv if sv else None, "min_value": mn, "format": "DD/MM/YYYY", "key": wkey}
        if mx:
            kw["max_value"] = mx
        return st.date_input(dlabel, **kw)
    if ftype == "time":
        return st.time_input(dlabel, value=sv if sv else None, step=1800, key=wkey)
    if ftype == "select":
        opts = field.get("options", [])
        idx  = opts.index(sv) if sv in opts else 0
        return st.selectbox(dlabel, opts, index=idx, key=wkey)
    return st.text_input(dlabel, value=sv or "", placeholder=ph, key=wkey)
 
 
# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────
 
def validate_raw(field: dict, value) -> str | None:
    ftype = field.get("type", "text")
    label = field.get("label", field["key"])
    if ftype == "derived":
        return None
    if field.get("required"):
        if value is None:
            return f"<b>{label}</b> e obrigatorio."
        if isinstance(value, str) and not value.strip():
            return f"<b>{label}</b> e obrigatorio."
        if isinstance(value, (int, float)) and value == 0:
            return f"<b>{label}</b> nao pode ser zero."
    if ftype == "cpf" and value and not CPF_RE.match(str(value).strip()):
        return f"<b>{label}</b> deve estar no formato 123.456.789-00."
    return None
 
def check_time_pairs(contract: dict, raw: dict) -> list:
    errors, checked = [], set()
    for section in contract.get("sections", []):
        for field in section.get("fields", []):
            end_key = field.get("time_end_key")
            if end_key and field["key"] not in checked:
                sv, ev = raw.get(field["key"]), raw.get(end_key)
                if sv and ev and ev <= sv:
                    end_label = next(
                        (f["label"] for s in contract["sections"]
                         for f in s["fields"] if f["key"] == end_key), end_key)
                    errors.append(f"<b>{end_label}</b> deve ser depois do horario de inicio.")
                checked.update([field["key"], end_key])
    return errors
 
 
# ─────────────────────────────────────────────
# CONTEXT BUILDER
# ─────────────────────────────────────────────
 
def build_context(contract: dict, raw: dict) -> dict:
    all_fields = {f["key"]: f for s in contract.get("sections", []) for f in s.get("fields", [])}
    ctx = {}
    for key, value in raw.items():
        field = all_fields.get(key, {})
        ftype = field.get("type", "text")
        if ftype == "derived" or value is None:
            ctx[key] = ""
            continue
        if ftype == "date":
            ctx[key] = value.strftime("%d/%m/%Y")
            dk = field.get("derive_weekday")
            if dk:
                ctx[dk] = WEEKDAYS_PT[value.weekday()]
        elif ftype == "time":
            ctx[key] = value.strftime("%H:%M")
        elif ftype == "currency":
            ctx[key] = format_brl(float(value))
        elif ftype == "number":
            ctx[key] = int(value)
        else:
            ctx[key] = value
    return ctx
 
 
# ─────────────────────────────────────────────
# CSS INJECTION
# ─────────────────────────────────────────────
 
def inject_css(cfg: dict, theme: str):
    p = "dark_" if theme == "dark" else "light_"
 
    bg_from = cfg[f"{p}bg_from"]
    bg_mid  = cfg[f"{p}bg_mid"]
    bg_to   = cfg[f"{p}bg_to"]
    surface = cfg[f"{p}surface"]
    surf_b  = cfg[f"{p}surface_border"]
    t_main  = cfg[f"{p}text_main"]
    t_sub   = cfg[f"{p}text_sub"]
    t_label = cfg[f"{p}text_label"]
    inp_bg  = cfg[f"{p}input_bg"]
    inp_b   = cfg[f"{p}input_border"]
 
    acc   = cfg["accent_color"]
    acc_h = cfg["accent_hover"]
    acc_s = cfg["accent_success"]
    acc_sh= cfg["accent_success_hover"]
    fh    = cfg["font_heading"]
    fb    = cfg["font_body"]
    gurl  = cfg["font_google_url"]
    r_c   = cfg["border_radius_card"]
    r_i   = cfg["border_radius_input"]
    r_b   = cfg["border_radius_button"]
 
    if theme == "dark":
        footer_bg  = f"linear-gradient(90deg,{bg_from}f0 0%,{bg_mid}f0 100%)"
        footer_b   = "rgba(96,165,250,0.1)"
        ghost_bg   = "rgba(255,255,255,0.05)"
        ghost_b    = "rgba(96,165,250,0.2)"
        ghost_c    = "#a8c4f0"
        ghost_hbg  = "rgba(96,165,250,0.12)"
        ghost_hb   = "rgba(96,165,250,0.45)"
        ghost_hc   = "#e8f0fe"
        divider_c  = "rgba(96,165,250,0.1)"
        section_b  = "rgba(96,165,250,0.08)"
        pill_bg    = f"rgba(96,165,250,0.08)"
        pill_b     = "rgba(96,165,250,0.2)"
        pill_c     = "#7bafd4"
        active_pill_bg = f"{acc}22"
        active_pill_b  = f"{acc}55"
        active_pill_c  = "#fff"
        done_pill_bg   = f"{acc_s}18"
        done_pill_b    = f"{acc_s}44"
        done_pill_c    = f"{acc_s}"
        err_bg  = "rgba(239,68,68,0.08)"
        err_b   = "rgba(239,68,68,0.25)"
        err_c   = "#fca5a5"
        err_li  = "#f87171"
        warn_c  = "#fbbf24"
        mesh_c1 = f"{acc}18"
        mesh_c2 = f"{acc_s}10"
    else:
        footer_bg  = f"linear-gradient(90deg,{bg_mid}f8 0%,{bg_from}f8 100%)"
        footer_b   = "rgba(0,0,0,0.07)"
        ghost_bg   = "rgba(0,0,0,0.03)"
        ghost_b    = "rgba(0,0,0,0.12)"
        ghost_c    = "#4a6a9a"
        ghost_hbg  = f"{acc}0a"
        ghost_hb   = f"{acc}44"
        ghost_hc   = acc
        divider_c  = "rgba(0,0,0,0.07)"
        section_b  = "rgba(0,0,0,0.06)"
        pill_bg    = "rgba(0,0,0,0.04)"
        pill_b     = "rgba(0,0,0,0.1)"
        pill_c     = "#6b7fa3"
        active_pill_bg = f"{acc}15"
        active_pill_b  = f"{acc}44"
        active_pill_c  = acc
        done_pill_bg   = f"{acc_s}12"
        done_pill_b    = f"{acc_s}40"
        done_pill_c    = "#0b8f5c"
        err_bg  = "rgba(220,38,38,0.05)"
        err_b   = "rgba(220,38,38,0.18)"
        err_c   = "#dc2626"
        err_li  = "#b91c1c"
        warn_c  = "#92400e"
        mesh_c1 = f"{acc}0a"
        mesh_c2 = f"{acc_s}08"
 
    st.markdown(f"""
<style>
@import url('{gurl}');
 
/* ─── Reset & base ─── */
html, body, [class*="css"] {{ font-family: '{fb}', sans-serif !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
section[data-testid="stSidebar"] {{ display: none !important; }}
 
/* ─── App background with mesh ─── */
.stApp {{
    background:
        radial-gradient(ellipse at 20% 20%, {mesh_c1} 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, {mesh_c2} 0%, transparent 50%),
        linear-gradient(135deg, {bg_from} 0%, {bg_mid} 50%, {bg_to} 100%);
    min-height: 100vh;
}}
 
/* ─── Content container ─── */
.block-container {{
    padding-top: 0 !important;
    padding-bottom: 80px !important;
    max-width: 1100px !important;
}}
 
/* ─── Typography ─── */
h1,h2,h3 {{ font-family: '{fh}', sans-serif !important; color: {t_main} !important; }}
 
/* ─── Form labels ─── */
label, .stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label,
.stTimeInput label, .stTextArea label {{
    color: {t_label} !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}}
 
/* ─── Inputs ─── */
.stTextInput input, .stNumberInput input, [data-baseweb="input"] input {{
    background: {inp_bg} !important;
    border: 1.5px solid {inp_b} !important;
    border-radius: {r_i} !important;
    color: {t_main} !important;
    -webkit-text-fill-color: {t_main} !important;
    font-family: '{fb}', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
    padding: 10px 14px !important;
}}
.stTextInput input:focus, [data-baseweb="input"] input:focus {{
    border-color: {acc} !important;
    box-shadow: 0 0 0 3px {acc}1a !important;
}}
.stTextInput input::placeholder, [data-baseweb="input"] input::placeholder {{
    color: {t_sub} !important; opacity: 0.55 !important;
}}
.stTextArea textarea {{
    background: {inp_bg} !important;
    border: 1.5px solid {inp_b} !important;
    border-radius: {r_i} !important;
    color: {t_main} !important;
    -webkit-text-fill-color: {t_main} !important;
    font-family: '{fb}', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
}}
.stTextArea textarea:focus {{
    border-color: {acc} !important;
    box-shadow: 0 0 0 3px {acc}1a !important;
}}
[data-baseweb="select"] > div {{
    background: {inp_bg} !important;
    border: 1.5px solid {inp_b} !important;
    border-radius: {r_i} !important;
    color: {t_main} !important;
    transition: border-color 0.18s !important;
}}
[data-baseweb="select"] span, [data-baseweb="select"] div,
[data-baseweb="select"] input, [data-baseweb="base-input"],
[data-baseweb="base-input"] > div, [data-baseweb="base-input"] input,
[data-baseweb="base-input"] span, [data-baseweb="input"] div,
[data-baseweb="input"] span {{
    color: {t_main} !important;
    -webkit-text-fill-color: {t_main} !important;
    background: transparent !important;
}}
.stNumberInput button {{ color: {t_main} !important; }}
[data-baseweb="menu"] li, [data-baseweb="menu"] div {{
    background: {inp_bg} !important; color: {t_main} !important;
}}
[data-baseweb="option"]:hover {{ background: {acc}18 !important; }}
 
/* ─── Primary button ─── */
.stButton button[kind="primary"],
.stFormSubmitButton button[kind="primary"] {{
    background: linear-gradient(135deg, {acc} 0%, {acc_h} 100%) !important;
    border: none !important;
    border-radius: {r_b} !important;
    color: #fff !important;
    font-family: '{fb}', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 16px {acc}44 !important;
}}
.stButton button[kind="primary"]:hover,
.stFormSubmitButton button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px {acc}66 !important;
}}
.stButton button[kind="primary"]:active,
.stFormSubmitButton button[kind="primary"]:active {{
    transform: translateY(0) scale(0.98) !important;
}}
 
/* ─── Secondary button ─── */
.stButton button[kind="secondary"] {{
    background: {ghost_bg} !important;
    border: 1.5px solid {ghost_b} !important;
    border-radius: {r_b} !important;
    color: {ghost_c} !important;
    font-family: '{fb}', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}}
.stButton button[kind="secondary"]:hover {{
    background: {ghost_hbg} !important;
    border-color: {ghost_hb} !important;
    color: {ghost_hc} !important;
    transform: translateY(-1px) !important;
}}
 
/* ─── Download button ─── */
.stDownloadButton button {{
    background: linear-gradient(135deg, {acc_s} 0%, {acc_sh} 100%) !important;
    border: none !important;
    border-radius: {r_b} !important;
    color: #fff !important;
    font-family: '{fb}', sans-serif !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 16px {acc_s}44 !important;
    transition: all 0.2s ease !important;
}}
.stDownloadButton button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px {acc_s}66 !important;
}}
 
/* ─── Misc ─── */
.stAlert {{ border-radius: {r_c} !important; border: none !important; }}
hr {{ border-color: {divider_c} !important; margin: 0 !important; }}
.stCaption, small {{ color: {t_sub} !important; font-size: 0.75rem !important; }}
.stSpinner > div {{ border-top-color: {acc} !important; }}
 
/* ─── Sticky footer ─── */
.sticky-footer {{
    position: fixed;
    bottom: 0; left: 0; right: 0;
    z-index: 999;
    background: {footer_bg};
    border-top: 1px solid {footer_b};
    padding: 10px 40px;
    display: flex;
    align-items: center;
    gap: 16px;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}}
.footer-sair-btn {{
    background: {ghost_bg};
    border: 1px solid {ghost_b};
    border-radius: 8px;
    color: {ghost_c};
    font-family: '{fb}', sans-serif;
    font-size: 0.8rem;
    font-weight: 500;
    padding: 6px 16px;
    transition: all 0.18s ease;
    text-decoration: none;
    white-space: nowrap;
}}
.footer-sair-btn:hover {{
    background: {ghost_hbg};
    border-color: {ghost_hb};
    color: {ghost_hc};
}}
 
/* ─── Top bar ─── */
.top-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 0 16px;
    border-bottom: 1px solid {divider_c};
    margin-bottom: 32px;
}}
.top-bar-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.top-bar-name {{
    font-family: '{fh}', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: {t_main};
    letter-spacing: -0.01em;
    margin: 0;
}}
.top-bar-sub {{
    font-size: 0.72rem;
    color: {t_sub};
    margin: 1px 0 0;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-weight: 500;
}}
 
/* ─── Selection screen ─── */
.select-heading {{
    font-family: '{fh}', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: {t_main};
    margin: 0 0 8px;
    letter-spacing: -0.03em;
}}
.select-sub {{
    font-size: 0.9rem;
    color: {t_sub};
    margin: 0 0 40px;
    line-height: 1.6;
}}
.contract-card {{
    background: {surface};
    border: 1.5px solid {surf_b};
    border-radius: {r_c};
    padding: 36px 28px 28px;
    text-align: center;
    transition: border-color 0.22s, box-shadow 0.22s, transform 0.22s;
    position: relative;
    overflow: hidden;
}}
.contract-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, {acc}, {acc_s});
    opacity: 0;
    transition: opacity 0.22s;
    border-radius: {r_c} {r_c} 0 0;
}}
.contract-card:hover {{
    border-color: {acc}55;
    box-shadow: 0 16px 48px {acc}18;
    transform: translateY(-5px);
}}
.contract-card:hover::before {{ opacity: 1; }}
.contract-card-icon {{
    font-size: 2.6rem;
    margin-bottom: 16px;
    display: block;
}}
.contract-card-name {{
    font-family: '{fh}', sans-serif !important;
    font-size: 1.05rem;
    font-weight: 700;
    color: {t_main} !important;
    margin: 0 0 8px;
    letter-spacing: -0.01em;
}}
.contract-card-desc {{
    font-size: 0.8rem;
    color: {t_sub} !important;
    margin: 0;
    line-height: 1.6;
}}
 
/* ─── Form screen ─── */
.form-header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 28px;
    gap: 16px;
}}
.form-title-wrap {{}}
.form-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: {t_main};
    margin: 0 0 4px;
    letter-spacing: -0.02em;
}}
.form-subtitle {{
    font-size: 0.82rem;
    color: {t_sub};
    margin: 0;
    line-height: 1.5;
}}
 
/* ─── Step progress pills ─── */
.step-pills {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 28px;
}}
.step-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 99px;
    font-family: '{fb}', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border: 1px solid {pill_b};
    background: {pill_bg};
    color: {pill_c};
    transition: all 0.18s ease;
    white-space: nowrap;
}}
.step-pill.active {{
    background: {active_pill_bg};
    border-color: {active_pill_b};
    color: {active_pill_c};
    box-shadow: 0 2px 8px {acc}22;
}}
.step-pill.done {{
    background: {done_pill_bg};
    border-color: {done_pill_b};
    color: {done_pill_c};
}}
.step-pill-dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
}}
 
/* ─── Section label ─── */
.section-label {{
    font-family: '{fh}', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {t_label};
    margin-top: 28px;
    padding-top: 22px;
    border-top: 1px solid {section_b};
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.section-icon {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px; height: 22px;
    background: {acc}18;
    border: 1px solid {acc}35;
    border-radius: 6px;
    font-size: 0.7rem;
}}
 
/* ─── Breadcrumb ─── */
.breadcrumb {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}}
.breadcrumb-root {{ font-size: 0.75rem; color: {t_sub}; cursor: pointer; }}
.breadcrumb-sep  {{ font-size: 0.75rem; color: {t_sub}; opacity: 0.4; }}
.breadcrumb-active {{
    font-size: 0.75rem;
    font-weight: 600;
    color: {t_label};
}}
 
/* ─── Confirm voltar ─── */
.voltar-confirm {{
    background: rgba(251,191,36,0.08);
    border: 1px solid rgba(251,191,36,0.25);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.82rem;
    color: {warn_c};
    margin-bottom: 8px;
}}
 
/* ─── Success ─── */
.success-card {{
    background: linear-gradient(135deg, {acc_s}14 0%, {acc_s}06 100%);
    border: 1.5px solid {acc_s}40;
    border-radius: {r_c};
    padding: 48px 40px 40px;
    text-align: center;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}}
.success-card::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, {acc_s}, {acc});
    border-radius: {r_c} {r_c} 0 0;
}}
.success-icon {{ font-size: 3.2rem; display: block; margin-bottom: 16px; }}
.success-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    color: {t_main};
    margin: 0 0 6px;
    letter-spacing: -0.02em;
}}
.success-name {{
    font-size: 0.88rem;
    color: {acc_s};
    font-weight: 500;
    margin: 0;
}}
 
/* ─── Error box ─── */
.err-box {{
    background: {err_bg};
    border: 1px solid {err_b};
    border-radius: {r_c};
    padding: 16px 20px;
    margin-top: 16px;
}}
.err-title {{
    color: {err_c};
    font-weight: 600;
    font-size: 0.82rem;
    margin: 0 0 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.err-list {{
    color: {err_li};
    font-size: 0.8rem;
    margin: 0;
    padding-left: 18px;
    line-height: 1.8;
}}
 
/* ─── Login ─── */
.login-wrap {{
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px 120px;
}}
.login-card {{
    background: {surface};
    border: 1.5px solid {surf_b};
    border-radius: 20px;
    padding: 40px 36px;
    width: 100%;
    max-width: 400px;
    backdrop-filter: blur(20px);
}}
.login-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: {t_main};
    text-align: center;
    margin: 0 0 6px;
    letter-spacing: -0.02em;
}}
.login-sub {{
    font-size: 0.82rem;
    color: {t_sub};
    text-align: center;
    margin: 0 0 28px;
    line-height: 1.5;
}}
</style>
""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# BOOTSTRAP
# ─────────────────────────────────────────────
 
cfg       = load_app_config()
contracts = load_contracts()
LOGO_B64  = get_logo_b64(cfg["logo"])
 
st.set_page_config(
    page_title=f"{cfg['app_name']} — Contratos",
    page_icon="📄",
    layout="wide",
)
 
if "theme" not in st.session_state:
    st.session_state.theme = cfg.get("default_theme", "dark")
 
if st.query_params.get("sair") == "1":
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()
 
inject_css(cfg, st.session_state.theme)
 
# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
 
for k, v in [
    ("authenticated",    False),
    ("contract_id",      None),
    ("confirm_voltar",   False),
    ("generated_docx",   None),
    ("generated_filename", None),
    ("show_preview",     False),
    ("saved_form_values", {}),
]:
    if k not in st.session_state:
        st.session_state[k] = v
 
 
# ─────────────────────────────────────────────
# PASSWORD GATE
# ─────────────────────────────────────────────
 
if not st.session_state.authenticated:
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
 
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        if LOGO_B64:
            st.markdown(f"""<div style="text-align:center;margin-bottom:28px;">
                <img src="data:image/png;base64,{LOGO_B64}"
                     style="max-width:160px;width:100%;"/>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="text-align:center;margin-bottom:28px;">
                <span style="font-family:'{cfg['font_heading']}',sans-serif;
                    font-size:1.6rem;font-weight:800;color:{cfg.get('dark_text_main','#e8f0fe')};">
                    {cfg['app_name']}
                </span>
            </div>""", unsafe_allow_html=True)
 
        st.markdown(f"""<div class="login-card">
            <p class="login-title">Bem-vindo</p>
            <p class="login-sub">{cfg['app_subtitle']}</p>
        </div>""", unsafe_allow_html=True)
 
        pw = st.text_input("Senha", type="password", placeholder="Digite sua senha",
                           label_visibility="collapsed")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
 
        if st.button("Entrar  →", use_container_width=True, type="primary"):
            if pw == cfg["password"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
 
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        tc1, tc2 = st.columns(2)
        with tc1:
            if st.button("☀️ Claro", use_container_width=True):
                st.session_state.theme = "light"; st.rerun()
        with tc2:
            if st.button("🌙 Escuro", use_container_width=True):
                st.session_state.theme = "dark"; st.rerun()
 
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()
 
 
# ─────────────────────────────────────────────
# STICKY FOOTER
# ─────────────────────────────────────────────
 
t  = st.session_state.theme
bg = cfg[f"{'dark' if t=='dark' else 'light'}_bg_from"]
tm = cfg[f"{'dark' if t=='dark' else 'light'}_text_main"]
 
logo_html = (
    f'<img src="data:image/png;base64,{LOGO_B64}" style="height:28px;opacity:0.9;"/>'
    if LOGO_B64 else
    f'<span style="font-family:{cfg["font_heading"]},sans-serif;font-size:0.85rem;'
    f'font-weight:700;color:{tm};">{cfg["app_name"]}</span>'
)
st.markdown(f"""<div class="sticky-footer">
    {logo_html}
    <a href="?sair=1" class="footer-sair-btn" target="_self">🚪 Sair</a>
</div>""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# TOP BAR
# ─────────────────────────────────────────────
 
tb1, tb2 = st.columns([5, 1])
with tb1:
    logo_top = (
        f'<img src="data:image/png;base64,{LOGO_B64}" style="height:32px;"/>'
        if LOGO_B64 else ""
    )
    st.markdown(f"""<div class="top-bar">
        <div class="top-bar-brand">
            {logo_top}
            <div>
                <p class="top-bar-name">{cfg['app_name']}</p>
                <p class="top-bar-sub">{cfg['app_subtitle']}</p>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
with tb2:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    tlabel = "☀️ Claro" if st.session_state.theme == "dark" else "🌙 Escuro"
    if st.button(tlabel, use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
 
 
# ─────────────────────────────────────────────
# CONTRACT SELECTION
# ─────────────────────────────────────────────
 
if st.session_state.contract_id is None:
    st.session_state.update(
        confirm_voltar=False, generated_docx=None,
        generated_filename=None, show_preview=False
    )
 
    st.markdown(f"""
    <p class="select-heading">Gerar contrato</p>
    <p class="select-sub">Selecione o tipo de contrato que deseja criar.</p>
    """, unsafe_allow_html=True)
 
    n    = len(contracts)
    cols = st.columns(max(n, 1), gap="large")
 
    for i, contract in enumerate(contracts):
        with cols[i % len(cols)]:
            st.markdown(f"""
            <div class="contract-card">
                <span class="contract-card-icon">{contract.get('icon','📄')}</span>
                <p class="contract-card-name">{contract['name']}</p>
                <p class="contract-card-desc">{contract.get('description','')}</p>
            </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button("Selecionar  →", key=f"sel_{contract['_id']}",
                         use_container_width=True, type="primary"):
                st.session_state.contract_id = contract["_id"]
                st.rerun()
 
    st.stop()
 
 
# ─────────────────────────────────────────────
# LOAD ACTIVE CONTRACT
# ─────────────────────────────────────────────
 
active = next((c for c in contracts if c["_id"] == st.session_state.contract_id), None)
if active is None:
    st.error("Contrato nao encontrado.")
    st.session_state.contract_id = None
    st.rerun()
 
 
# ─────────────────────────────────────────────
# SUCCESS STATE
# ─────────────────────────────────────────────
 
if st.session_state.generated_docx is not None:
    docx_bytes   = st.session_state.generated_docx
    filename     = st.session_state.generated_filename
    name_display = filename.replace("contrato_","").replace(".docx","").replace("_"," ")
 
    st.markdown(f"""<div class="success-card">
        <span class="success-icon">✅</span>
        <p class="success-title">Contrato gerado!</p>
        <p class="success-name">{name_display}</p>
    </div>""", unsafe_allow_html=True)
 
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        st.download_button(
            "📄  Baixar contrato", data=docx_bytes, file_name=filename,
            use_container_width=True,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    with c2:
        plabel = "🙈  Fechar preview" if st.session_state.show_preview else "👁  Visualizar"
        if st.button(plabel, use_container_width=True):
            st.session_state.show_preview = not st.session_state.show_preview
            st.rerun()
    with c3:
        if st.button("✏️  Editar", use_container_width=True):
            st.session_state.update(
                generated_docx=None, generated_filename=None,
                show_preview=False, confirm_voltar=False
            )
            st.rerun()
    with c4:
        if st.button("📝  Novo", use_container_width=True):
            st.session_state.update(
                generated_docx=None, generated_filename=None,
                show_preview=False, contract_id=None, saved_form_values={}
            )
            st.rerun()
 
    if st.session_state.show_preview:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        show_contract_preview(docx_bytes)
 
    st.stop()
 
 
# ─────────────────────────────────────────────
# BREADCRUMB + BACK
# ─────────────────────────────────────────────
 
bc, cc = st.columns([2, 5])
with bc:
    if not st.session_state.confirm_voltar:
        if st.button("← Voltar", key="btn_voltar"):
            st.session_state.confirm_voltar = True
            st.rerun()
    else:
        st.markdown('<div class="voltar-confirm">⚠️ Perder os dados preenchidos?</div>',
                    unsafe_allow_html=True)
        x1, x2 = st.columns(2)
        with x1:
            if st.button("Sim, voltar", use_container_width=True):
                st.session_state.update(contract_id=None, confirm_voltar=False,
                                        saved_form_values={})
                st.rerun()
        with x2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.confirm_voltar = False
                st.rerun()
 
with cc:
    st.markdown(f"""<div class="breadcrumb" style="padding-top:8px;">
        <span class="breadcrumb-root">Contratos</span>
        <span class="breadcrumb-sep">›</span>
        <span class="breadcrumb-active">{active.get('icon','')} {active['name']}</span>
    </div>""", unsafe_allow_html=True)
 
st.markdown('<hr/>', unsafe_allow_html=True)
st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# FORM HEADER + STEP PILLS
# ─────────────────────────────────────────────
 
sections     = active.get("sections", [])
total_secs   = len(sections)
saved        = st.session_state.saved_form_values
 
# Build step pills — a section is "done" if all its required fields have saved values
def section_done(section: dict) -> bool:
    for f in section.get("fields", []):
        if f.get("required") and f.get("type") != "derived":
            v = saved.get(f["key"])
            if v is None or (isinstance(v, str) and not v.strip()):
                return False
    return bool(saved)  # only show done if form was previously submitted
 
pills_html = '<div class="step-pills">'
for i, sec in enumerate(sections):
    is_done = section_done(sec)
    cls  = "done" if is_done else "step-pill"
    dot  = "✓" if is_done else f"{i+1}"
    pills_html += f'<span class="step-pill {cls}"><span class="step-pill-dot" style="{"width:8px;height:8px;border-radius:50%;background:currentColor;flex-shrink:0" if not is_done else ""}"></span>{sec["label"]}</span>'
pills_html += "</div>"
 
st.markdown(f"""
<div style="margin:20px 0 4px;">
    <p class="form-title">{active.get('icon','')} {active['name']}</p>
    <p class="form-subtitle">{active.get('description','')}</p>
</div>
{pills_html}
""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# DYNAMIC FORM
# ─────────────────────────────────────────────
 
form_key   = f"form_{active['_id']}"
raw_values = {}
 
with st.form(form_key):
    for section in sections:
        st.markdown(f"""<div class="section-label">
            <span class="section-icon">{section.get('icon','')}</span>
            {section['label']}
        </div>""", unsafe_allow_html=True)
 
        visible = [f for f in section.get("fields", []) if f.get("type") != "derived"]
 
        i = 0
        while i < len(visible):
            batch = visible[i:i + 3]
            cols  = st.columns(len(batch))
            for col, field in zip(cols, batch):
                with col:
                    raw_values[field["key"]] = render_field(
                        field, form_key, st.session_state.saved_form_values
                    )
            i += 3
 
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.caption("* Campos obrigatorios")
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    submit = st.form_submit_button(
        "Gerar contrato  →", type="primary", use_container_width=True
    )
 
 
# ─────────────────────────────────────────────
# SUBMISSION
# ─────────────────────────────────────────────
 
if submit:
    all_fields = {
        f["key"]: f
        for s in active.get("sections", [])
        for f in s.get("fields", [])
    }
    errors  = [e for k, v in raw_values.items()
               if (e := validate_raw(all_fields.get(k, {}), v))]
    errors += check_time_pairs(active, raw_values)
 
    if errors:
        items = "".join(f"<li>{e}</li>" for e in errors)
        st.markdown(f"""<div class="err-box">
            <p class="err-title">⚠️ Corrija os campos abaixo antes de continuar</p>
            <ul class="err-list">{items}</ul>
        </div>""", unsafe_allow_html=True)
    else:
        try:
            context  = build_context(active, raw_values)
            tpl_path = resolve_template(active["template"], active["_id"])
            st.session_state.generated_docx     = render_docx(tpl_path, context)
            st.session_state.generated_filename  = build_filename(active, context)
            st.session_state.saved_form_values   = raw_values
            st.session_state.show_preview        = False
            st.rerun()
        except FileNotFoundError:
            st.error(f"Template '{active['template']}' nao encontrado em contracts/.")