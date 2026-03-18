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

def format_brl_written(value: float) -> str:
    """Convert a float BRL value to written Portuguese. E.g. 1500.0 -> 'mil e quinhentos reais'"""
    ones     = ["","um","dois","tres","quatro","cinco","seis","sete","oito","nove","dez",
                "onze","doze","treze","quatorze","quinze","dezesseis","dezessete","dezoito","dezenove"]
    tens     = ["","","vinte","trinta","quarenta","cinquenta","sessenta","setenta","oitenta","noventa"]
    hundreds = ["","cem","duzentos","trezentos","quatrocentos","quinhentos",
                "seiscentos","setecentos","oitocentos","novecentos"]
    def _u1000(n):
        if n == 0: return ""
        if n == 100: return "cem"
        parts = []
        if n >= 100:
            parts.append(hundreds[n // 100]); n %= 100
        if n >= 20:
            t = tens[n // 10]; r = ones[n % 10]
            parts.append(f"{t} e {r}" if r else t)
        elif n > 0:
            parts.append(ones[n])
        return " e ".join(p for p in parts if p)
    value   = round(value, 2)
    reais   = int(value)
    cents   = round((value - reais) * 100)
    parts   = []
    bilhoes = reais // 1_000_000_000
    milhoes = (reais % 1_000_000_000) // 1_000_000
    mil     = (reais % 1_000_000) // 1_000
    resto   = reais % 1_000
    if bilhoes: parts.append(f"{_u1000(bilhoes)} {'bilhao' if bilhoes==1 else 'bilhoes'}")
    if milhoes: parts.append(f"{_u1000(milhoes)} {'milhao' if milhoes==1 else 'milhoes'}")
    if mil:
        parts.append("mil" if mil == 1 else f"{_u1000(mil)} mil")
    if resto:   parts.append(_u1000(resto))
    reais_str = " e ".join(p for p in parts if p)
    if reais > 0:
        reais_str = f"{reais_str} {'real' if reais==1 else 'reais'}"
    cents_str = f"{_u1000(cents)} {'centavo' if cents==1 else 'centavos'}" if cents > 0 else ""
    if reais_str and cents_str: return f"{reais_str} e {cents_str}"
    return reais_str or cents_str or "zero reais"

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
# FIELD RENDERER (outside form — for wizard)
# ─────────────────────────────────────────────

def render_field_free(field: dict, saved: dict, step_idx: int = 0):
    """Render a field outside st.form using unique session-state keys."""
    ftype  = field.get("type", "text")
    if ftype in ("derived", "currency_written"):
        return None
    key     = field["key"]
    label   = field.get("label", key)
    req     = field.get("required", False)
    ph      = field.get("placeholder", "")
    default = field.get("default", "")
    wkey    = f"wiz_s{step_idx}_{key}"
    dlabel  = f"{label} *" if req else label
    # Use saved value if available, otherwise fall back to JSON default
    sv      = saved.get(key) if saved.get(key) is not None else (default or None)

    if ftype in ("text", "cpf"):
        return st.text_input(dlabel, value=sv or "", placeholder=ph, key=wkey)
    if ftype == "textarea":
        return st.text_area(dlabel, value=sv or "", placeholder=ph, height=100, key=wkey)
    if ftype == "number":
        return st.number_input(dlabel, min_value=0,
                               value=int(sv) if sv is not None else None,
                               step=1, placeholder=ph, key=wkey)
    if ftype == "currency":
        return st.number_input(dlabel, min_value=0.0,
                               value=float(sv) if sv is not None else None,
                               step=50.0, placeholder=ph, key=wkey)
    if ftype == "date":
        past   = field.get("past_only", False)
        future = field.get("future_only", False)
        mn  = date(1920,1,1) if past else (date.today() if future else date(1920,1,1))
        mx  = date.today() if past else None
        kw  = {"value": sv if sv else None, "min_value": mn,
               "format": "DD/MM/YYYY", "key": wkey}
        if mx:
            kw["max_value"] = mx
        return st.date_input(dlabel, **kw)
    if ftype == "time":
        return st.time_input(dlabel, value=sv if sv else None, step=1800, key=wkey)
    if ftype == "select":
        opts = field.get("options", [])
        idx  = opts.index(sv) if sv in (opts or []) else 0
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

def validate_section(section: dict, saved: dict) -> list:
    errors = []
    for f in section.get("fields", []):
        err = validate_raw(f, saved.get(f["key"]))
        if err:
            errors.append(err)
    return errors


# ─────────────────────────────────────────────
# CONTEXT BUILDER
# ─────────────────────────────────────────────

def build_context(contract: dict, raw: dict) -> dict:
    all_fields = {f["key"]: f for s in contract.get("sections", []) for f in s.get("fields", [])}
    ctx = {}

    # First pass: process all real input fields
    for key, value in raw.items():
        field = all_fields.get(key, {})
        ftype = field.get("type", "text")
        if ftype in ("derived", "currency_written") or value is None:
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
            ctx[key] = f"{format_brl(float(value))} ({format_brl_written(float(value))})"
        elif ftype == "number":
            ctx[key] = int(value)
        else:
            ctx[key] = value

    # Second pass: compute all currency_written fields from their source
    # Also generate a _combined variable with "R$ X,XX (written form)"
    for key, field in all_fields.items():
        if field.get("type") == "currency_written":
            src_key = field.get("derived_from", "")
            src_val = raw.get(src_key)
            try:
                fv = float(src_val) if src_val else 0.0
                written = format_brl_written(fv)
                numeric = format_brl(fv)
                ctx[key] = f"{numeric} ({written})"
            except (TypeError, ValueError):
                ctx[key] = ""


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
        glass_bg      = "rgba(255,255,255,0.04)"
        glass_border  = "rgba(255,255,255,0.10)"
        footer_bg     = "rgba(6,13,31,0.85)"
        footer_b      = "rgba(255,255,255,0.08)"
        ghost_bg      = "rgba(255,255,255,0.06)"
        ghost_b       = "rgba(255,255,255,0.12)"
        ghost_c       = "#a8c4f0"
        ghost_hbg     = "rgba(255,255,255,0.10)"
        ghost_hb      = "rgba(255,255,255,0.22)"
        ghost_hc      = "#e8f0fe"
        divider_c     = "rgba(255,255,255,0.07)"
        section_b     = "rgba(255,255,255,0.06)"
        step_inactive_bg  = "rgba(255,255,255,0.04)"
        step_inactive_b   = "rgba(255,255,255,0.10)"
        step_inactive_c   = "#5a7aa0"
        step_active_bg    = acc + "28"
        step_active_b     = acc + "77"
        step_active_c     = "#fff"
        step_done_bg      = acc_s + "20"
        step_done_b       = acc_s + "60"
        step_done_c       = acc_s
        err_bg  = "rgba(239,68,68,0.10)"
        err_b   = "rgba(239,68,68,0.28)"
        err_c   = "#fca5a5"
        err_li  = "#f87171"
        warn_c  = "#fbbf24"
        mesh_c1 = acc + "20"
        mesh_c2 = acc_s + "12"
        mesh_c3 = "rgba(120,80,255,0.10)"
        track_bg   = "rgba(255,255,255,0.08)"
        track_fill = acc
        inp_glass  = "rgba(255,255,255,0.05)"
        inp_glass_b= "rgba(255,255,255,0.12)"
    else:
        glass_bg      = "rgba(255,255,255,0.55)"
        glass_border  = "rgba(255,255,255,0.75)"
        footer_bg     = "rgba(240,244,255,0.85)"
        footer_b      = "rgba(0,0,0,0.08)"
        ghost_bg      = "rgba(255,255,255,0.50)"
        ghost_b       = "rgba(0,0,0,0.12)"
        ghost_c       = "#4a6a9a"
        ghost_hbg     = acc + "0d"
        ghost_hb      = acc + "44"
        ghost_hc      = acc
        divider_c     = "rgba(0,0,0,0.07)"
        section_b     = "rgba(0,0,0,0.06)"
        step_inactive_bg  = "rgba(255,255,255,0.60)"
        step_inactive_b   = "rgba(0,0,0,0.10)"
        step_inactive_c   = "#8a9abf"
        step_active_bg    = acc + "14"
        step_active_b     = acc + "44"
        step_active_c     = acc
        step_done_bg      = acc_s + "12"
        step_done_b       = acc_s + "44"
        step_done_c       = "#0b8f5c"
        err_bg  = "rgba(220,38,38,0.06)"
        err_b   = "rgba(220,38,38,0.20)"
        err_c   = "#dc2626"
        err_li  = "#b91c1c"
        warn_c  = "#92400e"
        mesh_c1 = acc + "0c"
        mesh_c2 = acc_s + "08"
        mesh_c3 = "rgba(120,80,255,0.05)"
        track_bg   = "rgba(0,0,0,0.08)"
        track_fill = acc
        inp_glass  = "rgba(255,255,255,0.70)"
        inp_glass_b= "rgba(255,255,255,0.90)" 

    st.markdown(f"""
<style>
@import url('{gurl}');

html, body, [class*="css"] {{ font-family: '{fb}', sans-serif !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
section[data-testid="stSidebar"] {{ display: none !important; }}

/* ── Animated background with orbs ── */
.stApp {{
    background:
        radial-gradient(ellipse at 10% 10%, {mesh_c1} 0%, transparent 45%),
        radial-gradient(ellipse at 90% 90%, {mesh_c2} 0%, transparent 45%),
        radial-gradient(ellipse at 60% 20%, {mesh_c3} 0%, transparent 40%),
        linear-gradient(135deg, {bg_from} 0%, {bg_mid} 50%, {bg_to} 100%);
    min-height: 100vh;
}}
.block-container {{
    padding-top: 0 !important;
    padding-bottom: 100px !important;
    max-width: 100% !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
}}

h1,h2,h3 {{ font-family: '{fh}', sans-serif !important; color: {t_main} !important; }}

/* ── Labels ── */
label, .stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label,
.stTimeInput label, .stTextArea label {{
    color: {t_label} !important;
    font-size: 0.71rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}}

/* ── Glass inputs ── */
.stTextInput input, .stNumberInput input, [data-baseweb="input"] input {{
    background: {inp_glass} !important;
    border: 1px solid {inp_glass_b} !important;
    border-radius: {r_i} !important;
    color: {t_main} !important;
    -webkit-text-fill-color: {t_main} !important;
    font-family: '{fb}', sans-serif !important;
    font-size: 0.9rem !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
}}
.stTextInput input:focus, [data-baseweb="input"] input:focus {{
    border-color: {acc} !important;
    box-shadow: 0 0 0 3px {acc}22, inset 0 1px 0 rgba(255,255,255,0.1) !important;
    outline: none !important;
}}
.stTextInput input::placeholder, [data-baseweb="input"] input::placeholder {{
    color: {t_sub} !important; opacity: 0.5 !important;
}}
.stTextArea textarea {{
    background: {inp_glass} !important;
    border: 1px solid {inp_glass_b} !important;
    border-radius: {r_i} !important;
    color: {t_main} !important;
    -webkit-text-fill-color: {t_main} !important;
    font-family: '{fb}', sans-serif !important;
    font-size: 0.9rem !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
}}
.stTextArea textarea:focus {{
    border-color: {acc} !important;
    box-shadow: 0 0 0 3px {acc}22 !important;
}}
[data-baseweb="select"] > div {{
    background: {inp_glass} !important;
    border: 1px solid {inp_glass_b} !important;
    border-radius: {r_i} !important;
    color: {t_main} !important;
    backdrop-filter: blur(10px) !important;
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
[data-baseweb="menu"] li {{
    background: {inp_bg} !important;
    color: {t_main} !important;
    backdrop-filter: blur(20px) !important;
}}
[data-baseweb="option"]:hover {{ background: {acc}18 !important; }}

/* ── Primary button ── */
.stButton button[kind="primary"] {{
    background: linear-gradient(135deg, {acc} 0%, {acc_h} 100%) !important;
    border: none !important;
    border-radius: {r_b} !important;
    color: #fff !important;
    font-family: '{fb}', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 20px {acc}55, inset 0 1px 0 rgba(255,255,255,0.2) !important;
}}
.stButton button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px {acc}77, inset 0 1px 0 rgba(255,255,255,0.25) !important;
}}
.stButton button[kind="primary"]:active {{
    transform: translateY(0) scale(0.98) !important;
}}

/* ── Ghost button ── */
.stButton button[kind="secondary"] {{
    background: {ghost_bg} !important;
    border: 1px solid {ghost_b} !important;
    border-radius: {r_b} !important;
    color: {ghost_c} !important;
    font-family: '{fb}', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    transition: all 0.2s ease !important;
}}
.stButton button[kind="secondary"]:hover {{
    background: {ghost_hbg} !important;
    border-color: {ghost_hb} !important;
    color: {ghost_hc} !important;
    transform: translateY(-1px) !important;
}}

/* ── Download button ── */
.stDownloadButton button {{
    background: linear-gradient(135deg, {acc_s} 0%, {acc_sh} 100%) !important;
    border: none !important;
    border-radius: {r_b} !important;
    color: #fff !important;
    font-family: '{fb}', sans-serif !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 20px {acc_s}55, inset 0 1px 0 rgba(255,255,255,0.2) !important;
    transition: all 0.2s ease !important;
}}
.stDownloadButton button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px {acc_s}77 !important;
}}

/* ── Misc ── */
.stAlert {{ border-radius: {r_c} !important; border: none !important; }}
hr {{ border-color: {divider_c} !important; margin: 0 !important; }}
.stCaption, small {{ color: {t_sub} !important; font-size: 0.73rem !important; }}
.stSpinner > div {{ border-top-color: {acc} !important; }}

/* ── Sticky footer — glass ── */
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
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    box-shadow: 0 -1px 0 {footer_b}, 0 -8px 32px rgba(0,0,0,0.15);
}}
.footer-sair-btn {{
    background: {ghost_bg};
    border: 1px solid {ghost_b};
    border-radius: 8px;
    color: {ghost_c};
    font-family: '{fb}', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 6px 14px;
    transition: all 0.18s;
    text-decoration: none;
    white-space: nowrap;
    backdrop-filter: blur(10px);
}}
.footer-sair-btn:hover {{
    background: {ghost_hbg};
    border-color: {ghost_hb};
    color: {ghost_hc};
}}

/* ── Top bar — glass ── */
.top-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px 16px;
    margin: 0 -3rem 32px;
    background: {glass_bg};
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid {glass_border};
    box-shadow: 0 1px 0 rgba(255,255,255,0.04), 0 4px 24px rgba(0,0,0,0.08);
}}
.top-bar-left {{ display: flex; align-items: center; gap: 12px; }}
.top-bar-name {{
    font-family: '{fh}', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: {t_main};
    margin: 0;
    letter-spacing: -0.01em;
}}
.top-bar-sub {{
    font-size: 0.7rem;
    color: {t_sub};
    margin: 2px 0 0;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-weight: 500;
}}

/* ── Select screen ── */
.select-heading {{
    font-family: '{fh}', sans-serif;
    font-size: 2.1rem;
    font-weight: 800;
    color: {t_main};
    margin: 0 0 8px;
    letter-spacing: -0.03em;
    line-height: 1.2;
}}
.select-sub {{
    font-size: 0.88rem;
    color: {t_sub};
    margin: 0 0 40px;
}}

/* ── Contract cards — glass ── */
.contract-card {{
    background: {glass_bg};
    border: 1px solid {glass_border};
    border-radius: {r_c};
    padding: 36px 28px 28px;
    text-align: center;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.08);
    transition: border-color 0.22s, box-shadow 0.22s, transform 0.22s;
    position: relative;
    overflow: hidden;
}}
.contract-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
}}
.contract-card:hover {{
    border-color: {acc}66;
    box-shadow: 0 16px 48px {acc}22, 0 4px 16px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.12);
    transform: translateY(-5px);
}}
.contract-card-icon {{ font-size:2.8rem; margin-bottom:16px; display:block; }}
.contract-card-name {{
    font-family:'{fh}',sans-serif !important;
    font-size:1.05rem; font-weight:700;
    color:{t_main} !important; margin:0 0 8px;
}}
.contract-card-desc {{ font-size:0.8rem; color:{t_sub} !important; margin:0; line-height:1.6; }}

/* ── Wizard progress bar ── */
.wizard-header {{ margin-bottom: 28px; }}
.wizard-meta {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 14px;
}}
.wizard-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: {t_main};
    margin: 0;
    letter-spacing: -0.02em;
}}
.wizard-counter {{
    font-size: 0.75rem;
    font-weight: 600;
    color: {t_sub};
    letter-spacing: 0.06em;
    text-transform: uppercase;
    white-space: nowrap;
}}
.progress-track {{
    height: 3px;
    background: {track_bg};
    border-radius: 99px;
    overflow: hidden;
    margin-bottom: 20px;
}}
.progress-fill {{
    height: 100%;
    background: linear-gradient(90deg, {track_fill}, {acc_s});
    border-radius: 99px;
    transition: width 0.4s cubic-bezier(.22,.68,0,1.2);
    box-shadow: 0 0 8px {track_fill}88;
}}
.step-list {{
    display: flex;
    gap: 0;
    overflow-x: auto;
    padding-bottom: 2px;
    scrollbar-width: none;
}}
.step-list::-webkit-scrollbar {{ display: none; }}
.step-item {{ display: flex; align-items: center; flex-shrink: 0; }}
.step-btn {{
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 6px 14px 6px 10px;
    border-radius: 99px;
    font-family: '{fb}', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    border: 1px solid {step_inactive_b};
    background: {step_inactive_bg};
    color: {step_inactive_c};
    white-space: nowrap;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: all 0.18s;
}}
.step-btn.active {{
    background: {step_active_bg};
    border-color: {step_active_b};
    color: {step_active_c};
    box-shadow: 0 2px 12px {acc}33;
}}
.step-btn.done {{
    background: {step_done_bg};
    border-color: {step_done_b};
    color: {step_done_c};
}}
.step-num {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 18px; height: 18px;
    border-radius: 50%;
    font-size: 0.65rem; font-weight: 700;
    background: currentColor;
    color: transparent;
    flex-shrink: 0;
    position: relative;
}}
.step-num::after {{
    content: attr(data-n);
    position: absolute;
    color: {bg_from};
    font-size: 0.62rem; font-weight: 700;
}}
.step-num.done-num::after {{ content: '✓'; }}
.step-connector {{
    width: 24px; height: 1.5px;
    background: {step_inactive_b};
    flex-shrink: 0; margin: 0 -2px;
}}
.step-connector.done {{ background: {step_done_b}; }}

/* ── Section header ── */
.section-header {{ margin-bottom: 24px; }}
.section-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.1rem; font-weight: 700;
    color: {t_main};
    margin: 0 0 4px;
    letter-spacing: -0.01em;
    display: flex; align-items: center; gap: 10px;
}}
.section-icon-lg {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 34px; height: 34px;
    background: {glass_bg};
    border: 1px solid {glass_border};
    border-radius: 10px;
    font-size: 1rem; flex-shrink: 0;
    backdrop-filter: blur(10px);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);
}}

/* ── Breadcrumb ── */
.breadcrumb {{ display: flex; align-items: center; gap: 8px; margin-bottom: 24px; }}
.bc-root {{ font-size: 0.73rem; color: {t_sub}; }}
.bc-sep  {{ font-size: 0.73rem; color: {t_sub}; opacity: 0.35; }}
.bc-active {{ font-size: 0.73rem; font-weight: 600; color: {t_label}; }}

/* ── Confirm voltar ── */
.voltar-box {{
    background: rgba(251,191,36,0.08);
    border: 1px solid rgba(251,191,36,0.22);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 0.8rem;
    color: {warn_c};
    margin-bottom: 8px;
    backdrop-filter: blur(10px);
}}

/* ── Success card — glass ── */
.success-card {{
    background: {glass_bg};
    border: 1px solid {acc_s}44;
    border-radius: {r_c};
    padding: 48px 40px 40px;
    text-align: center;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    box-shadow: 0 16px 48px rgba(0,0,0,0.15), 0 0 0 1px rgba(255,255,255,0.06), inset 0 1px 0 rgba(255,255,255,0.10);
}}
.success-card::before {{
    content:'';
    position:absolute;
    top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,{acc_s},{acc});
    border-radius:{r_c} {r_c} 0 0;
    opacity:0.9;
}}
.success-card::after {{
    content:'';
    position:absolute;
    inset:0;
    background: radial-gradient(ellipse at 50% 0%, {acc_s}12 0%, transparent 60%);
    pointer-events:none;
}}
.success-icon {{ font-size:3.2rem; display:block; margin-bottom:16px; position:relative; z-index:1; }}
.success-title {{
    font-family:'{fh}',sans-serif;
    font-size:1.5rem; font-weight:800;
    color:{t_main}; margin:0 0 6px;
    letter-spacing:-0.02em;
    position:relative; z-index:1;
}}
.success-name {{ font-size:0.88rem; color:{acc_s}; font-weight:500; margin:0; position:relative; z-index:1; }}

/* ── Error box ── */
.err-box {{
    background:{err_bg};
    border:1px solid {err_b};
    border-radius:{r_c};
    padding:14px 18px; margin-top:14px;
    backdrop-filter: blur(10px);
}}
.err-title {{ color:{err_c}; font-weight:600; font-size:0.8rem; margin:0 0 8px; }}
.err-list {{ color:{err_li}; font-size:0.78rem; margin:0; padding-left:16px; line-height:1.9; }}

/* ── Login card — glass ── */
.login-outer {{
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    min-height:80vh; padding:0 0 80px;
}}
.login-logo {{ text-align:center; margin-bottom:28px; }}
.login-card {{
    background: {glass_bg};
    border: 1px solid {glass_border};
    border-radius: 20px;
    padding: 36px 32px 28px;
    width: 100%;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    box-shadow: 0 24px 64px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.10);
    position: relative;
    overflow: hidden;
}}
.login-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
}}
.login-title {{
    font-family:'{fh}',sans-serif;
    font-size:1.4rem; font-weight:800;
    color:{t_main}; text-align:center;
    margin:0 0 4px; letter-spacing:-0.02em;
}}
.login-sub {{
    font-size:0.8rem; color:{t_sub};
    text-align:center; margin:0 0 24px;
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
    ("authenticated",     False),
    ("contract_id",       None),
    ("wizard_step",       0),
    ("wizard_values",     {}),
    ("confirm_voltar",    False),
    ("generated_docx",   None),
    ("generated_filename", None),
    ("show_preview",      False),
]:
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# PASSWORD GATE
# ─────────────────────────────────────────────

if not st.session_state.authenticated:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)

        if LOGO_B64:
            st.markdown(f"""<div class="login-logo">
                <img src="data:image/png;base64,{LOGO_B64}"
                     style="max-width:150px;width:100%;"/>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="login-logo">
                <span style="font-family:'{cfg['font_heading']}',sans-serif;
                    font-size:1.6rem;font-weight:800;">
                    {cfg['app_name']}
                </span>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="login-card">
            <p class="login-title">Bem-vindo</p>
            <p class="login-sub">{cfg['app_subtitle']}</p>
        </div>""", unsafe_allow_html=True)

        pw = st.text_input("Senha de acesso", type="password",
                           placeholder="Digite sua senha",
                           label_visibility="collapsed")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if st.button("Entrar  →", use_container_width=True, type="primary"):
            if pw == cfg["password"]:
                st.session_state.authenticated = True
                st.rerun()
            elif pw:
                st.error("Senha incorreta.")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        tc1, tc2 = st.columns(2)
        with tc1:
            if st.button("☀️ Claro", use_container_width=True):
                st.session_state.theme = "light"; st.rerun()
        with tc2:
            if st.button("🌙 Escuro", use_container_width=True):
                st.session_state.theme = "dark"; st.rerun()

    st.stop()


# ─────────────────────────────────────────────
# STICKY FOOTER
# ─────────────────────────────────────────────

tm = cfg[f"{'dark' if st.session_state.theme=='dark' else 'light'}_text_main"]
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
        f'<img src="data:image/png;base64,{LOGO_B64}" style="height:30px;"/>'
        if LOGO_B64 else ""
    )
    st.markdown(f"""<div class="top-bar">
        <div class="top-bar-left">
            {logo_top}
            <div>
                <p class="top-bar-name">{cfg['app_name']}</p>
                <p class="top-bar-sub">{cfg['app_subtitle']}</p>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
with tb2:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    tl = "☀️ Claro" if st.session_state.theme == "dark" else "🌙 Escuro"
    if st.button(tl, use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()


# ─────────────────────────────────────────────
# CONTRACT SELECTION
# ─────────────────────────────────────────────

if st.session_state.contract_id is None:
    st.session_state.update(
        confirm_voltar=False, generated_docx=None,
        generated_filename=None, show_preview=False,
        wizard_step=0, wizard_values={}
    )

    st.markdown("""
    <p class="select-heading">Gerar contrato</p>
    <p class="select-sub">Selecione o tipo de contrato que deseja criar.</p>
    """, unsafe_allow_html=True)

    cols = st.columns(max(len(contracts), 1), gap="large")
    for i, contract in enumerate(contracts):
        with cols[i % len(cols)]:
            st.markdown(f"""<div class="contract-card">
                <span class="contract-card-icon">{contract.get('icon','📄')}</span>
                <p class="contract-card-name">{contract['name']}</p>
                <p class="contract-card-desc">{contract.get('description','')}</p>
            </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button("Selecionar  →", key=f"sel_{contract['_id']}",
                         use_container_width=True, type="primary"):
                st.session_state.contract_id = contract["_id"]
                st.session_state.wizard_step = 0
                # Seed wizard_values with any JSON defaults so they pre-fill correctly
                defaults = {
                    f["key"]: f["default"]
                    for s in contract.get("sections", [])
                    for f in s.get("fields", [])
                    if "default" in f and f.get("type") not in ("derived", "currency_written")
                }
                st.session_state.wizard_values = defaults
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

sections   = active.get("sections", [])
total_steps = len(sections)


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
        pl = "🙈  Fechar preview" if st.session_state.show_preview else "👁  Visualizar"
        if st.button(pl, use_container_width=True):
            st.session_state.show_preview = not st.session_state.show_preview
            st.rerun()
    with c3:
        if st.button("✏️  Editar", use_container_width=True):
            # Go back to last wizard step with values pre-filled
            st.session_state.update(
                generated_docx=None, generated_filename=None,
                show_preview=False, wizard_step=total_steps - 1
            )
            st.rerun()
    with c4:
        if st.button("📝  Novo", use_container_width=True):
            st.session_state.update(
                generated_docx=None, generated_filename=None,
                show_preview=False, contract_id=None,
                wizard_step=0, wizard_values={}
            )
            st.rerun()

    if st.session_state.show_preview:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        show_contract_preview(docx_bytes)
    st.stop()


# ─────────────────────────────────────────────
# BREADCRUMB
# ─────────────────────────────────────────────

st.markdown(f"""<div class="breadcrumb">
    <span class="bc-root">Contratos</span>
    <span class="bc-sep">›</span>
    <span class="bc-root">{active.get('icon','')} {active['name']}</span>
    <span class="bc-sep">›</span>
    <span class="bc-active">{sections[st.session_state.wizard_step]['label']}</span>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# WIZARD PROGRESS HEADER
# ─────────────────────────────────────────────

step_idx   = st.session_state.wizard_step
pct        = int(((step_idx) / total_steps) * 100)
cur_section = sections[step_idx]

# Build step list HTML
steps_html = '<div class="step-list">'
for i, sec in enumerate(sections):
    is_done   = i < step_idx
    is_active = i == step_idx
    cls = "done" if is_done else ("active" if is_active else "")
    num_cls = "done-num" if is_done else ""
    num_content = "✓" if is_done else str(i + 1)
    connector_cls = "done" if i < step_idx else ""

    steps_html += f"""<div class="step-item">
        <div class="step-btn {cls}">
            <span class="step-num {num_cls}" data-n="{num_content}"></span>
            {sec['label']}
        </div>
    </div>"""
    if i < total_steps - 1:
        steps_html += f'<div class="step-connector {connector_cls}"></div>'
steps_html += "</div>"

st.markdown(f"""<div class="wizard-header">
    <div class="wizard-meta">
        <p class="wizard-title">{active.get('icon','')} {active['name']}</p>
        <span class="wizard-counter">Etapa {step_idx + 1} de {total_steps}</span>
    </div>
    <div class="progress-track">
        <div class="progress-fill" style="width:{pct}%"></div>
    </div>
    {steps_html}
</div>""", unsafe_allow_html=True)

st.markdown('<hr/>', unsafe_allow_html=True)
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CURRENT STEP FIELDS
# ─────────────────────────────────────────────

st.markdown(f"""<div class="section-header">
    <p class="section-title">
        <span class="section-icon-lg">{cur_section.get('icon','')}</span>
        {cur_section['label']}
    </p>
</div>""", unsafe_allow_html=True)

visible = [f for f in cur_section.get("fields", []) if f.get("type") != "derived"]
step_raw = {}

i = 0
while i < len(visible):
    batch = visible[i:i + 3]
    cols  = st.columns(len(batch))
    for col, field in zip(cols, batch):
        with col:
            step_raw[field["key"]] = render_field_free(
                field, st.session_state.wizard_values
            )
    i += 3

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
st.caption("* Campos obrigatorios")
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# WIZARD NAVIGATION
# ─────────────────────────────────────────────

is_last = (step_idx == total_steps - 1)

nav_left, nav_right = st.columns([1, 1])

with nav_left:
    if step_idx == 0:
        # First step — back goes to contract selection
        if not st.session_state.confirm_voltar:
            if st.button("← Trocar contrato", use_container_width=True):
                st.session_state.confirm_voltar = True
                st.rerun()
        else:
            st.markdown('<div class="voltar-box">⚠️ Perder os dados preenchidos?</div>',
                        unsafe_allow_html=True)
            cx1, cx2 = st.columns(2)
            with cx1:
                if st.button("Sim", use_container_width=True):
                    st.session_state.update(
                        contract_id=None, confirm_voltar=False,
                        wizard_step=0, wizard_values={}
                    )
                    st.rerun()
            with cx2:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.confirm_voltar = False
                    st.rerun()
    else:
        if st.button("← Etapa anterior", use_container_width=True):
            # Save current step values before going back
            st.session_state.wizard_values.update(step_raw)
            st.session_state.wizard_step -= 1
            st.session_state.confirm_voltar = False
            st.rerun()

with nav_right:
    if not is_last:
        if st.button("Proxima etapa  →", use_container_width=True, type="primary"):
            # Validate this step
            errors = []
            all_fields_map = {f["key"]: f for f in cur_section.get("fields", [])}
            for k, v in step_raw.items():
                err = validate_raw(all_fields_map.get(k, {}), v)
                if err:
                    errors.append(err)

            if errors:
                items = "".join(f"<li>{e}</li>" for e in errors)
                st.markdown(f"""<div class="err-box">
                    <p class="err-title">⚠️ Corrija antes de continuar</p>
                    <ul class="err-list">{items}</ul>
                </div>""", unsafe_allow_html=True)
            else:
                st.session_state.wizard_values.update(step_raw)
                st.session_state.wizard_step += 1
                st.session_state.confirm_voltar = False
                st.rerun()
    else:
        if st.button("Gerar contrato  →", use_container_width=True, type="primary"):
            # Merge last step and validate everything
            all_values = {**st.session_state.wizard_values, **step_raw}
            all_fields_map = {
                f["key"]: f
                for s in sections
                for f in s.get("fields", [])
            }
            errors  = [e for k, v in all_values.items()
                       if (e := validate_raw(all_fields_map.get(k, {}), v))]
            errors += check_time_pairs(active, all_values)

            if errors:
                items = "".join(f"<li>{e}</li>" for e in errors)
                st.markdown(f"""<div class="err-box">
                    <p class="err-title">⚠️ Corrija os campos abaixo</p>
                    <ul class="err-list">{items}</ul>
                </div>""", unsafe_allow_html=True)
            else:
                try:
                    context  = build_context(active, all_values)
                    tpl_path = resolve_template(active["template"], active["_id"])
                    st.session_state.generated_docx     = render_docx(tpl_path, context)
                    st.session_state.generated_filename  = build_filename(active, context)
                    st.session_state.wizard_values       = all_values
                    st.session_state.show_preview        = False
                    st.rerun()
                except FileNotFoundError:
                    st.error(f"Template '{active['template']}' nao encontrado em contracts/.")
