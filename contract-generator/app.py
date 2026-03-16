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
        "font_heading":         "Sora",
        "font_body":            "DM Sans",
        "font_google_url":      "https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Sora:wght@300;400;600;700;800&display=swap",
        "border_radius_card":   "20px",
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
    """Return the written Portuguese form of a BRL value.
    E.g. 2500.00 -> 'dois mil e quinhentos reais'
         1500.50 -> 'mil e quinhentos reais e cinquenta centavos'
    """
    ones      = ["", "um", "dois", "tres", "quatro", "cinco", "seis", "sete",
                 "oito", "nove", "dez", "onze", "doze", "treze", "quatorze",
                 "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
    tens      = ["", "", "vinte", "trinta", "quarenta", "cinquenta",
                 "sessenta", "setenta", "oitenta", "noventa"]
    hundreds  = ["", "cem", "duzentos", "trezentos", "quatrocentos",
                 "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"]
 
    def _under_1000(n: int) -> str:
        if n == 0:
            return ""
        if n == 100:
            return "cem"
        parts = []
        if n >= 100:
            parts.append(hundreds[n // 100])
            n %= 100
        if n >= 20:
            t = tens[n // 10]
            r = ones[n % 10]
            parts.append(f"{t} e {r}" if r else t)
        elif n > 0:
            parts.append(ones[n])
        return " e ".join(p for p in parts if p)
 
    def _chunk(n: int, singular: str, plural: str) -> str:
        s = _under_1000(n)
        if not s:
            return ""
        label = singular if n == 1 else plural
        return f"{s} {label}"
 
    value   = round(value, 2)
    reais   = int(value)
    cents   = round((value - reais) * 100)
 
    if reais == 0 and cents == 0:
        return "zero reais"
 
    parts = []
 
    bilhoes  = reais // 1_000_000_000
    milhoens = (reais % 1_000_000_000) // 1_000_000
    milhares = (reais % 1_000_000) // 1_000
    resto    = reais % 1_000
 
    if bilhoes:
        parts.append(_chunk(bilhoes, "bilhao", "bilhoes"))
    if milhoens:
        parts.append(_chunk(milhoens, "milhao", "milhoes"))
    if milhares:
        # In Portuguese, "mil" not "um mil"
        s = _under_1000(milhares)
        if milhares == 1:
            parts.append("mil")
        elif s:
            parts.append(f"{s} mil")
    if resto:
        parts.append(_under_1000(resto))
 
    reais_str = " e ".join(p for p in parts if p)
    if reais > 0:
        reais_label = "real" if reais == 1 else "reais"
        reais_str   = f"{reais_str} {reais_label}"
    else:
        reais_str = ""
 
    if cents > 0:
        cents_label = "centavo" if cents == 1 else "centavos"
        cents_str   = f"{_under_1000(cents)} {cents_label}"
    else:
        cents_str = ""
 
    if reais_str and cents_str:
        return f"{reais_str} e {cents_str}"
    return reais_str or cents_str
 
 
def get_logo_b64(filename: str) -> str:
    try:
        with open(os.path.join(BASE_DIR, filename), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""
 
 
def resolve_template(template_filename: str, contract_id: str) -> str:
    """
    Search for the template file in this order:
    1. contracts/<filename>
    2. <root>/<filename>
    3. contracts/<contract_id>.docx  (fallback by contract id)
    Raises FileNotFoundError with a helpful message if not found.
    """
    candidates = [
        os.path.join(CONTRACTS_DIR, template_filename),
        os.path.join(BASE_DIR, template_filename),
        os.path.join(CONTRACTS_DIR, f"{contract_id}.docx"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    checked = "\n  ".join(candidates)
    raise FileNotFoundError(
        f"Template '{template_filename}' not found. Checked:\n  {checked}"
    )
 
 
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
 
 
def docx_to_html(docx_bytes: bytes) -> str:
    import mammoth, io
    result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
    return result.value
 
 
def docx_to_pdf(docx_bytes: bytes) -> bytes | None:
    """
    Try to convert docx -> HTML -> PDF via weasyprint.
    Returns PDF bytes on success, None if weasyprint or its
    system dependencies are unavailable.
    """
    try:
        import weasyprint, io
        html_content = docx_to_html(docx_bytes)
        full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');
  body {{ font-family: 'DM Sans', Arial, sans-serif; font-size: 13px;
         line-height: 1.7; color: #111; margin: 60px 80px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
  td, th {{ border: 1px solid #ddd; padding: 6px 10px; }}
  p {{ margin: 6px 0; }}
</style>
</head><body>{html_content}</body></html>"""
        pdf_bytes = weasyprint.HTML(string=full_html).write_pdf()
        return pdf_bytes
    except Exception:
        return None
 
 
def show_contract_preview(docx_bytes: bytes):
    with st.spinner("Gerando pre-visualizacao..."):
        html_content = docx_to_html(docx_bytes)
    st.markdown(f"""
    <div style="background:#fff;padding:60px 80px;max-width:860px;margin:0 auto;
        font-family:'DM Sans',sans-serif;font-size:14px;line-height:1.7;color:#111;
        border:1px solid #ddd;border-radius:16px;box-shadow:0 8px 40px rgba(0,0,0,0.15);">
        {html_content}
    </div>""", unsafe_allow_html=True)
 
 
def build_filename(contract: dict, context: dict) -> str:
    parts = [
        str(context.get(k, "")).replace("/", "-").replace(" ", "_")
        for k in contract.get("filename_fields", [])
    ]
    slug = "_".join(p for p in parts if p)
    return f"contrato_{slug or contract.get('_id', 'contrato')}.docx"
 
 
# ─────────────────────────────────────────────
# CSS INJECTION (fully config-driven)
# ─────────────────────────────────────────────
 
def inject_css(cfg: dict, theme: str):
    p = "dark_" if theme == "dark" else "light_"
 
    bg_from  = cfg[f"{p}bg_from"]
    bg_mid   = cfg[f"{p}bg_mid"]
    bg_to    = cfg[f"{p}bg_to"]
    surface  = cfg[f"{p}surface"]
    surf_b   = cfg[f"{p}surface_border"]
    t_main   = cfg[f"{p}text_main"]
    t_sub    = cfg[f"{p}text_sub"]
    t_label  = cfg[f"{p}text_label"]
    inp_bg   = cfg[f"{p}input_bg"]
    inp_b    = cfg[f"{p}input_border"]
    inp_c    = t_main
 
    acc      = cfg["accent_color"]
    acc_h    = cfg["accent_hover"]
    acc_s    = cfg["accent_success"]
    acc_sh   = cfg["accent_success_hover"]
    fh       = cfg["font_heading"]
    fb       = cfg["font_body"]
    gurl     = cfg["font_google_url"]
    r_card   = cfg["border_radius_card"]
    r_input  = cfg["border_radius_input"]
    r_btn    = cfg["border_radius_button"]
 
    if theme == "dark":
        footer_bg    = f"linear-gradient(90deg,{bg_from} 0%,{bg_mid} 100%)"
        footer_b     = "rgba(96,165,250,0.12)"
        ghost_bg     = "rgba(255,255,255,0.05)"
        ghost_b      = "rgba(96,165,250,0.25)"
        ghost_c      = "#a8c4f0"
        ghost_hbg    = "rgba(96,165,250,0.1)"
        ghost_hb     = "rgba(96,165,250,0.5)"
        ghost_hc     = "#e8f0fe"
        section_b    = "rgba(96,165,250,0.1)"
        divider_c    = "rgba(96,165,250,0.12)"
        err_bg       = "rgba(255,80,80,0.08)"
        err_b        = "rgba(255,80,80,0.25)"
        err_c        = "#ff8080"
        err_li       = "#cc6060"
        crumb_c      = "#3a5a8a"
        crumb_sep    = "#2a3a5c"
        crumb_active = "#7bafd4"
        warn_c       = "#e8c060"
        login_card   = f"background:rgba(255,255,255,0.03);border:1px solid rgba(96,165,250,0.15);"
    else:
        footer_bg    = f"linear-gradient(90deg,{bg_mid} 0%,{bg_from} 100%)"
        footer_b     = "rgba(0,0,0,0.08)"
        ghost_bg     = "rgba(0,0,0,0.03)"
        ghost_b      = "rgba(0,0,0,0.15)"
        ghost_c      = "#3a5a9a"
        ghost_hbg    = "rgba(29,106,255,0.06)"
        ghost_hb     = "rgba(29,106,255,0.3)"
        ghost_hc     = "#1d3a8a"
        section_b    = "rgba(0,0,0,0.07)"
        divider_c    = "rgba(0,0,0,0.07)"
        err_bg       = "rgba(220,30,30,0.05)"
        err_b        = "rgba(220,30,30,0.2)"
        err_c        = "#cc2222"
        err_li       = "#993333"
        crumb_c      = "#8a9abf"
        crumb_sep    = "#c0cce0"
        crumb_active = "#3a5a9a"
        warn_c       = "#996600"
        login_card   = f"background:#fff;border:1px solid rgba(0,0,0,0.08);"
 
    st.markdown(f"""
<style>
@import url('{gurl}');
 
/* ── Keyframe animations ── */
@keyframes fadeSlideUp {{
    from {{ opacity: 0; transform: translateY(18px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to   {{ opacity: 1; }}
}}
@keyframes pulseGlow {{
    0%, 100% {{ box-shadow: 0 0 0 0 {acc}44; }}
    50%       {{ box-shadow: 0 0 0 8px {acc}00; }}
}}
@keyframes successPop {{
    0%   {{ transform: scale(0.85); opacity: 0; }}
    60%  {{ transform: scale(1.04); opacity: 1; }}
    100% {{ transform: scale(1); }}
}}
@keyframes shimmer {{
    0%   {{ background-position: -400px 0; }}
    100% {{ background-position: 400px 0; }}
}}
@keyframes cardFloat {{
    0%, 100% {{ transform: translateY(0px); }}
    50%       {{ transform: translateY(-4px); }}
}}
 
/* ── Custom cursor ── */
*, *::before, *::after {{
    cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='4' fill='{acc.replace('#','%23')}' opacity='0.9'/%3E%3Ccircle cx='12' cy='12' r='8' fill='none' stroke='{acc.replace('#','%23')}' stroke-width='1.5' opacity='0.4'/%3E%3C/svg%3E") 12 12, auto !important;
}}
button, a, [role="button"], .stButton button, .stDownloadButton button,
.stFormSubmitButton button, .footer-sair-btn, .contract-card {{
    cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 28 28'%3E%3Ccircle cx='14' cy='14' r='6' fill='{acc.replace('#','%23')}' opacity='1'/%3E%3Ccircle cx='14' cy='14' r='11' fill='none' stroke='{acc.replace('#','%23')}' stroke-width='1.5' opacity='0.6'/%3E%3C/svg%3E") 14 14, pointer !important;
}}
input, textarea, select {{
    cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='24' viewBox='0 0 20 24'%3E%3Crect x='9' y='0' width='2' height='24' fill='{acc.replace('#','%23')}' rx='1'/%3E%3Crect x='4' y='0' width='12' height='3' fill='{acc.replace('#','%23')}' rx='1'/%3E%3Crect x='4' y='21' width='12' height='3' fill='{acc.replace('#','%23')}' rx='1'/%3E%3C/svg%3E") 10 12, text !important;
}}
 
/* ── Base ── */
html, body, [class*="css"] {{ font-family: '{fb}', sans-serif !important; }}
.stApp {{
    background: linear-gradient(135deg, {bg_from} 0%, {bg_mid} 50%, {bg_to} 100%);
    min-height: 100vh;
    animation: fadeIn 0.4s ease;
}}
 
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{
    padding-top: 2rem !important;
    padding-bottom: 80px !important;
    animation: fadeSlideUp 0.45s cubic-bezier(.22,.68,0,1.2) both;
}}
section[data-testid="stSidebar"] {{ display: none !important; }}
 
h1,h2,h3 {{ font-family: '{fh}', sans-serif !important; color: {t_main} !important; }}
p, span, div {{ color: {t_main}; }}
 
/* ── Labels ── */
label, .stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label,
.stTimeInput label, .stTextArea label {{
    color: {t_label} !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    transition: color 0.2s !important;
}}
 
/* ── Inputs ── */
.stTextInput input, .stNumberInput input, [data-baseweb="input"] input {{
    background: {inp_bg} !important;
    border: 1px solid {inp_b} !important;
    border-radius: {r_input} !important;
    color: {inp_c} !important;
    font-family: '{fb}', sans-serif !important;
    transition: border-color 0.2s, box-shadow 0.2s, background 0.2s !important;
    -webkit-text-fill-color: {inp_c} !important;
}}
.stTextInput input:focus, .stNumberInput input:focus, [data-baseweb="input"] input:focus {{
    border-color: {acc} !important;
    box-shadow: 0 0 0 3px {acc}22 !important;
    -webkit-text-fill-color: {inp_c} !important;
}}
.stTextInput input::placeholder, .stNumberInput input::placeholder,
[data-baseweb="input"] input::placeholder {{
    color: {t_sub} !important;
    opacity: 0.6 !important;
}}
.stTextArea textarea {{
    background: {inp_bg} !important;
    border: 1px solid {inp_b} !important;
    border-radius: {r_input} !important;
    color: {inp_c} !important;
    -webkit-text-fill-color: {inp_c} !important;
    font-family: '{fb}', sans-serif !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
.stTextArea textarea:focus {{
    border-color: {acc} !important;
    box-shadow: 0 0 0 3px {acc}22 !important;
}}
.stTextArea textarea::placeholder {{
    color: {t_sub} !important;
    opacity: 0.6 !important;
}}
[data-baseweb="select"] > div {{
    background: {inp_bg} !important;
    border: 1px solid {inp_b} !important;
    border-radius: {r_input} !important;
    color: {inp_c} !important;
    transition: border-color 0.2s !important;
}}
[data-baseweb="select"] span,
[data-baseweb="select"] div,
[data-baseweb="select"] input {{
    color: {inp_c} !important;
    -webkit-text-fill-color: {inp_c} !important;
}}
[data-baseweb="base-input"] {{
    background: {inp_bg} !important;
    border-radius: {r_input} !important;
    color: {inp_c} !important;
    -webkit-text-fill-color: {inp_c} !important;
}}
[data-baseweb="base-input"] > div,
[data-baseweb="base-input"] input,
[data-baseweb="base-input"] span {{
    color: {inp_c} !important;
    -webkit-text-fill-color: {inp_c} !important;
    background: transparent !important;
}}
[data-baseweb="input"] div, [data-baseweb="input"] span {{
    color: {inp_c} !important;
    -webkit-text-fill-color: {inp_c} !important;
}}
.stNumberInput button {{ color: {inp_c} !important; }}
[data-baseweb="menu"] li, [data-baseweb="menu"] div {{
    background: {inp_bg} !important;
    color: {inp_c} !important;
}}
[data-baseweb="option"]:hover {{ background: {acc}22 !important; }}
 
/* ── Buttons ── */
.stButton button[kind="primary"],
.stFormSubmitButton button[kind="primary"] {{
    background: linear-gradient(135deg, {acc} 0%, {acc_h} 100%) !important;
    border: none !important;
    border-radius: {r_btn} !important;
    color: #fff !important;
    font-family: '{fb}', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    transition: all 0.22s cubic-bezier(.22,.68,0,1.2) !important;
    box-shadow: 0 4px 20px {acc}55 !important;
    position: relative !important;
    overflow: hidden !important;
}}
.stButton button[kind="primary"]:hover,
.stFormSubmitButton button[kind="primary"]:hover {{
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 8px 32px {acc}88 !important;
}}
.stButton button[kind="primary"]:active,
.stFormSubmitButton button[kind="primary"]:active {{
    transform: translateY(0) scale(0.98) !important;
}}
.stButton button[kind="secondary"] {{
    background: {ghost_bg} !important;
    border: 1px solid {ghost_b} !important;
    border-radius: {r_btn} !important;
    color: {ghost_c} !important;
    font-family: '{fb}', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}}
.stButton button[kind="secondary"]:hover {{
    background: {ghost_hbg} !important;
    border-color: {ghost_hb} !important;
    color: {ghost_hc} !important;
    transform: translateY(-1px) !important;
}}
.stDownloadButton button {{
    background: linear-gradient(135deg, {acc_s} 0%, {acc_sh} 100%) !important;
    border: none !important;
    border-radius: {r_btn} !important;
    color: #fff !important;
    font-family: '{fb}', sans-serif !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 20px {acc_s}55 !important;
    transition: all 0.22s cubic-bezier(.22,.68,0,1.2) !important;
}}
.stDownloadButton button:hover {{
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 8px 32px {acc_s}88 !important;
}}
 
/* ── Misc ── */
.stAlert {{ border-radius: {r_card} !important; border: none !important; animation: fadeSlideUp 0.3s ease; }}
hr {{ border-color: {divider_c} !important; }}
.stCaption, small {{ color: {t_sub} !important; }}
.stSpinner > div {{ border-top-color: {acc} !important; }}
 
/* ── Sticky footer ── */
.sticky-footer {{
    position: fixed;
    bottom: 0; left: 0; right: 0;
    z-index: 999;
    background: {footer_bg};
    border-top: 1px solid {footer_b};
    padding: 10px 32px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 20px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}}
.footer-sair-btn {{
    background: {ghost_bg};
    border: 1px solid {ghost_b};
    border-radius: 8px;
    color: {ghost_c};
    font-family: '{fb}', sans-serif;
    font-size: 0.82rem;
    font-weight: 500;
    padding: 7px 18px;
    transition: all 0.2s ease;
    text-decoration: none;
    letter-spacing: 0.02em;
}}
.footer-sair-btn:hover {{
    background: {ghost_hbg};
    border-color: {ghost_hb};
    color: {ghost_hc};
    transform: translateY(-1px);
}}
 
/* ── Section label ── */
.section-label {{
    font-family: '{fh}', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {t_label};
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid {section_b};
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 10px;
    animation: fadeSlideUp 0.3s ease both;
}}
.section-label span {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px; height: 22px;
    background: {acc}20;
    border: 1px solid {acc}40;
    border-radius: 6px;
    font-size: 0.72rem;
    transition: background 0.2s, transform 0.2s;
}}
.section-label:hover span {{
    background: {acc}35;
    transform: scale(1.1);
}}
 
/* ── Contract selection cards ── */
.contract-card {{
    background: {surface};
    border: 1px solid {surf_b};
    border-radius: {r_card};
    padding: 40px 32px 32px;
    text-align: center;
    transition: border-color 0.25s, box-shadow 0.25s, transform 0.25s;
    animation: fadeSlideUp 0.4s cubic-bezier(.22,.68,0,1.2) both;
}}
.contract-card:hover {{
    border-color: {acc}88;
    box-shadow: 0 12px 40px {acc}22;
    transform: translateY(-4px);
}}
.contract-card-icon {{
    font-size: 2.8rem;
    margin-bottom: 16px;
    display: block;
    animation: cardFloat 3s ease-in-out infinite;
}}
.contract-card-name {{
    font-family: '{fh}', sans-serif !important;
    font-size: 1.1rem;
    font-weight: 700;
    color: {t_main} !important;
    margin: 0 0 10px;
    letter-spacing: -0.01em;
}}
.contract-card-desc {{
    font-size: 0.82rem;
    color: {t_sub} !important;
    margin: 0;
    line-height: 1.6;
}}
 
/* ── Success card ── */
.success-card {{
    background: linear-gradient(135deg, {acc_s}18, {acc_s}06);
    border: 1px solid {acc_s}50;
    border-radius: {r_card};
    padding: 40px;
    text-align: center;
    margin-bottom: 28px;
    animation: successPop 0.5s cubic-bezier(.22,.68,0,1.2) both;
}}
.success-icon {{
    font-size: 3rem;
    margin-bottom: 14px;
    display: block;
    animation: successPop 0.6s cubic-bezier(.22,.68,0,1.2) 0.1s both;
}}
 
/* ── Typography helpers ── */
.page-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    color: {t_main};
    margin: 0;
    letter-spacing: -0.02em;
    animation: fadeSlideUp 0.4s ease both;
}}
.page-subtitle {{
    font-size: 0.85rem;
    color: {t_sub};
    margin: 4px 0 0;
    animation: fadeSlideUp 0.4s ease 0.05s both;
}}
.form-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: {t_main};
    margin: 0 0 4px;
    animation: fadeSlideUp 0.35s ease both;
}}
.form-subtitle {{
    font-size: 0.82rem;
    color: {t_sub};
    margin: 0 0 24px;
    animation: fadeSlideUp 0.35s ease 0.05s both;
}}
.success-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: {t_main};
    margin: 0 0 6px;
}}
.success-sub {{ font-size: 0.9rem; color: {acc_s}; margin: 0; font-weight: 500; }}
.warn-text {{ font-size: 0.8rem; color: {warn_c}; margin-bottom: 8px; font-weight: 500; }}
.err-box {{
    background: {err_bg};
    border: 1px solid {err_b};
    border-radius: {r_card};
    padding: 16px 20px;
    margin-top: 12px;
    animation: fadeSlideUp 0.3s ease both;
}}
.err-title {{ color: {err_c}; font-weight: 600; margin: 0 0 8px; font-size: 0.85rem; }}
.err-list {{ color: {err_li}; font-size: 0.82rem; margin: 0; padding-left: 18px; line-height: 1.8; }}
.crumb-root {{ font-size: 0.75rem; color: {crumb_c}; }}
.crumb-sep  {{ font-size: 0.75rem; color: {crumb_sep}; }}
.crumb-active {{ font-size: 0.75rem; font-weight: 600; color: {crumb_active}; }}
 
/* ── Login card ── */
.login-card {{
    {login_card}
    border-radius: {r_card};
    padding: 40px 36px 32px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    animation: fadeSlideUp 0.5s cubic-bezier(.22,.68,0,1.2) both;
}}
.login-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: {t_main};
    text-align: center;
    margin: 0 0 6px;
}}
.login-sub {{ font-size: 0.85rem; color: {t_sub}; text-align: center; margin: 0 0 28px; }}
 
/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
    background: {acc}44;
    border-radius: 99px;
}}
::-webkit-scrollbar-thumb:hover {{ background: {acc}88; }}
 
/* ── Selection highlight ── */
::selection {{ background: {acc}44; color: {t_main}; }}
</style>
.crumb-root {{ font-size: 0.75rem; color: {crumb_c}; }}
.crumb-sep  {{ font-size: 0.75rem; color: {crumb_sep}; }}
.crumb-active {{ font-size: 0.75rem; font-weight: 600; color: {crumb_active}; }}
 
/* ── Login card ── */
.login-card {{ {login_card} border-radius: {r_card}; padding: 40px 36px 32px; backdrop-filter: blur(12px); }}
.login-title {{
    font-family: '{fh}', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: {t_main};
    text-align: center;
    margin: 0 0 6px;
}}
.login-sub {{ font-size: 0.85rem; color: {t_sub}; text-align: center; margin: 0 0 28px; }}
</style>
""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# FIELD RENDERER
# ─────────────────────────────────────────────
 
def render_field(field: dict, form_key: str, saved: dict = None):
    ftype = field.get("type", "text")
    if ftype == "derived":
        return None
    key    = field["key"]
    label  = field.get("label", key)
    req    = field.get("required", False)
    ph     = field.get("placeholder", "")
    wkey   = f"{form_key}_{key}"
    dlabel = f"{label} *" if req else label
    sv     = (saved or {}).get(key)  # saved value from previous submission
 
    if ftype == "currency_written":
        return None  # auto-derived from paired currency field in build_context
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
        val = sv if sv else None
        kw  = {"value": val, "min_value": mn, "format": "DD/MM/YYYY", "key": wkey}
        if mx:
            kw["max_value"] = mx
        return st.date_input(dlabel, **kw)
    if ftype == "time":
        return st.time_input(dlabel, value=sv if sv else None, step=1800, key=wkey)
    if ftype == "select":
        opts  = field.get("options", [])
        idx   = opts.index(sv) if sv in opts else 0
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
    if ftype in ("derived", "currency_written"):
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
    all_fields = {
        f["key"]: f
        for s in contract.get("sections", [])
        for f in s.get("fields", [])
    }
    ctx = {}
    for key, value in raw.items():
        field = all_fields.get(key, {})
        ftype = field.get("type", "text")
        if ftype == "derived" or value is None:
            ctx[key] = ""
            continue
        if ftype == "date":
            ctx[key] = value.strftime("%d/%m/%Y")
            derive_key = field.get("derive_weekday")
            if derive_key:
                ctx[derive_key] = WEEKDAYS_PT[value.weekday()]
        elif ftype == "time":
            ctx[key] = value.strftime("%H:%M")
        elif ftype == "currency":
            fval = float(value)
            ctx[key]               = format_brl(fval)
            ctx[f"{key}_written"]  = format_brl_written(fval)
        elif ftype == "number":
            ctx[key] = int(value)
        else:
            ctx[key] = value
    return ctx
 
 
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
 
# Logout via query param
if st.query_params.get("sair") == "1":
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()
 
inject_css(cfg, st.session_state.theme)
 
# ─────────────────────────────────────────────
# PASSWORD GATE
# ─────────────────────────────────────────────
 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
 
if not st.session_state.authenticated:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
        if LOGO_B64:
            st.markdown(f"""<div style="text-align:center;margin-bottom:32px;">
                <img src="data:image/png;base64,{LOGO_B64}" style="max-width:180px;width:100%;"/>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="text-align:center;margin-bottom:32px;">
                <span style="font-family:'{cfg['font_heading']}',sans-serif;font-size:1.5rem;
                    font-weight:800;">{cfg['app_name']}</span>
            </div>""", unsafe_allow_html=True)
 
        st.markdown(f"""<div class="login-card">
            <p class="login-title">Bem-vindo</p>
            <p class="login-sub">{cfg['app_subtitle']}</p>
        </div>""", unsafe_allow_html=True)
 
        password = st.text_input("Senha", type="password", placeholder="••••••••",
                                 label_visibility="collapsed")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Entrar", use_container_width=True, type="primary"):
            if password == cfg["password"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
 
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        tc1, tc2 = st.columns(2)
        with tc1:
            if st.button("☀️ Modo Claro", use_container_width=True):
                st.session_state.theme = "light"; st.rerun()
        with tc2:
            if st.button("🌙 Modo Escuro", use_container_width=True):
                st.session_state.theme = "dark"; st.rerun()
    st.stop()
 
# ─────────────────────────────────────────────
# STICKY FOOTER
# ─────────────────────────────────────────────
 
logo_html = (
    f'<img src="data:image/png;base64,{LOGO_B64}" style="height:32px;opacity:0.88;"/>'
    if LOGO_B64 else
    f'<span style="font-family:{cfg["font_heading"]},sans-serif;font-size:0.85rem;'
    f'font-weight:700;letter-spacing:0.08em;">{cfg["app_name"]}</span>'
)
st.markdown(f"""<div class="sticky-footer">
    {logo_html}
    <a href="?sair=1" class="footer-sair-btn" target="_self">🚪 Sair</a>
</div>""", unsafe_allow_html=True)
 
# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
 
for k, v in [("contract_id", None), ("confirm_voltar", False),
              ("generated_docx", None), ("generated_filename", None),
              ("show_preview", False), ("saved_form_values", {})]:
    if k not in st.session_state:
        st.session_state[k] = v
 
# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────
 
hc1, hc2 = st.columns([5, 1])
with hc1:
    st.markdown(f"""
    <p class="page-title">{cfg['app_name']}</p>
    <p class="page-subtitle">{cfg['app_subtitle']}</p>""", unsafe_allow_html=True)
with hc2:
    tlabel = "☀️ Claro" if st.session_state.theme == "dark" else "🌙 Escuro"
    if st.button(tlabel, use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
 
st.markdown('<hr style="margin:16px 0 24px;"/>', unsafe_allow_html=True)
 
# ─────────────────────────────────────────────
# CONTRACT SELECTION
# ─────────────────────────────────────────────
 
if st.session_state.contract_id is None:
    for k in ("confirm_voltar","generated_docx","generated_filename","show_preview"):
        st.session_state[k] = False if k == "confirm_voltar" else None if k != "show_preview" else False
 
    st.markdown(f"""<p style="font-family:'{cfg['font_heading']}',sans-serif;
        font-size:0.7rem;font-weight:700;letter-spacing:0.14em;
        text-transform:uppercase;margin-bottom:20px;">
        Selecione o tipo de contrato</p>""", unsafe_allow_html=True)
 
    n    = len(contracts)
    cols = st.columns(n, gap="large") if n > 1 else st.columns([1, 1])
 
    for i, contract in enumerate(contracts):
        with cols[i]:
            delay = f"{i * 0.08:.2f}s"
            st.markdown(f"""
            <div class="contract-card" style="animation-delay:{delay}">
                <div class="contract-card-icon">{contract.get('icon','📄')}</div>
                <p class="contract-card-name">{contract['name']}</p>
                <p class="contract-card-desc">{contract.get('description','')}</p>
            </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
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
        <p class="success-sub">{name_display}</p>
    </div>""", unsafe_allow_html=True)
 
    # Try PDF conversion once and cache result in session state
    pdf_cache_key = f"pdf_{st.session_state.generated_filename}"
    if pdf_cache_key not in st.session_state:
        with st.spinner("Preparando PDF..."):
            st.session_state[pdf_cache_key] = docx_to_pdf(docx_bytes)
    pdf_bytes = st.session_state[pdf_cache_key]
 
    if pdf_bytes is not None:
        c1, c2, c3, c4, c5 = st.columns(5, gap="medium")
    else:
        c1, c2, c3, c4 = st.columns(4, gap="medium")
 
    with c1:
        st.download_button("📄  Baixar .docx", data=docx_bytes, file_name=filename,
                           use_container_width=True,
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
 
    if pdf_bytes is not None:
        with c2:
            pdf_filename = filename.replace(".docx", ".pdf")
            st.download_button("📕  Baixar PDF", data=pdf_bytes, file_name=pdf_filename,
                               use_container_width=True, mime="application/pdf")
    with c2:
        plabel = "🙈  Fechar preview" if st.session_state.show_preview else "👁  Pre-visualizar"
        if st.button(plabel, use_container_width=True):
            st.session_state.show_preview = not st.session_state.show_preview
            st.rerun()
    with c3:
        if st.button("✏️  Editar contrato", use_container_width=True):
            # Keep contract_id so the form reappears, just clear the generated doc
            st.session_state.update(generated_docx=None, generated_filename=None,
                                    show_preview=False, confirm_voltar=False)
            st.rerun()
    with c4:
        if st.button("📝  Novo contrato", use_container_width=True):
            st.session_state.update(generated_docx=None, generated_filename=None,
                                    show_preview=False, contract_id=None,
                                    saved_form_values={})
            st.rerun()
 
    if st.session_state.show_preview:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        show_contract_preview(docx_bytes)
    st.stop()
 
# ─────────────────────────────────────────────
# BACK BUTTON + BREADCRUMB
# ─────────────────────────────────────────────
 
bc, cc = st.columns([2, 5])
with bc:
    if not st.session_state.confirm_voltar:
        if st.button("← Voltar"):
            st.session_state.confirm_voltar = True
            st.rerun()
    else:
        st.markdown('<p class="warn-text">Perder os dados preenchidos?</p>', unsafe_allow_html=True)
        x1, x2 = st.columns(2)
        with x1:
            if st.button("Sim", use_container_width=True):
                st.session_state.contract_id = None
                st.session_state.confirm_voltar = False
                st.rerun()
        with x2:
            if st.button("Nao", use_container_width=True):
                st.session_state.confirm_voltar = False
                st.rerun()
with cc:
    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;padding-top:6px;">
        <span class="crumb-root">Contratos</span>
        <span class="crumb-sep">›</span>
        <span class="crumb-active">{active.get('icon','')} {active['name']}</span>
    </div>""", unsafe_allow_html=True)
 
st.markdown('<hr style="margin:16px 0 0;"/>', unsafe_allow_html=True)
 
# ─────────────────────────────────────────────
# FORM PAGE HEADER
# ─────────────────────────────────────────────
 
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
st.markdown(f"""
<p class="form-title">{active.get('icon','')} {active['name']}</p>
<p class="form-subtitle">{active.get('description','')}</p>
""", unsafe_allow_html=True)
 
# ─────────────────────────────────────────────
# DYNAMIC FORM
# ─────────────────────────────────────────────
 
form_key   = f"form_{active['_id']}"
raw_values = {}
 
with st.form(form_key):
    for section in active.get("sections", []):
        st.markdown(f"""<div class="section-label">
            <span>{section.get('icon','')}</span>
            {section['label']}
        </div>""", unsafe_allow_html=True)
 
        visible = [f for f in section.get("fields", []) if f.get("type") != "derived"]
 
        i = 0
        while i < len(visible):
            batch = visible[i:i + 3]
            cols  = st.columns(len(batch))
            for col, field in zip(cols, batch):
                with col:
                    raw_values[field["key"]] = render_field(field, form_key, st.session_state.saved_form_values)
            i += 3
 
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.caption("* Campos obrigatorios")
    submit = st.form_submit_button("Gerar contrato  →", type="primary", use_container_width=True)
 
# ─────────────────────────────────────────────
# SUBMISSION
# ─────────────────────────────────────────────
 
if submit:
    all_fields = {
        f["key"]: f
        for s in active.get("sections", [])
        for f in s.get("fields", [])
    }
    errors = [e for k, v in raw_values.items()
              if (e := validate_raw(all_fields.get(k, {}), v))]
    errors += check_time_pairs(active, raw_values)
 
    if errors:
        st.markdown(f"""<div class="err-box">
            <p class="err-title">Corrija os campos abaixo:</p>
            <ul class="err-list">{"".join(f'<li>{e}</li>' for e in errors)}</ul>
        </div>""", unsafe_allow_html=True)
    else:
        try:
            context  = build_context(active, raw_values)
            tpl_path = resolve_template(active["template"], active["_id"])
            st.session_state.generated_docx    = render_docx(tpl_path, context)
            st.session_state.generated_filename = build_filename(active, context)
            st.session_state.saved_form_values  = raw_values
            st.session_state.show_preview       = False
            st.rerun()
        except FileNotFoundError:
            st.error(f"Template '{active['template']}' nao encontrado. Verifique se o arquivo .docx esta na pasta contracts/ ou na raiz do projeto.")