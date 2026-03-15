import re
import os
import base64
import tempfile
from datetime import date
 
import streamlit as st
from docxtpl import DocxTemplate
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
BIG_TEMPLATE    = os.path.join(BASE_DIR, "contract_template.docx")
POCKET_TEMPLATE = os.path.join(BASE_DIR, "pocket_template.docx")
LOGO_PATH       = os.path.join(BASE_DIR, "logo.png")
 
WEEKDAYS_PT = {
    0: "Segunda-feira", 1: "Terca-feira", 2: "Quarta-feira",
    3: "Quinta-feira",  4: "Sexta-feira", 5: "Sabado", 6: "Domingo",
}
 
CPF_PATTERN = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
 
 
# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
 
def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
 
def validate_cpf_format(cpf: str) -> bool:
    return bool(CPF_PATTERN.match(cpf.strip()))
 
def validate_fields(fields: dict) -> list:
    errors = []
    for label, value in fields.items():
        if isinstance(value, str) and not value.strip():
            errors.append(f"<b>{label}</b> e obrigatorio.")
        elif isinstance(value, (int, float)) and value == 0:
            errors.append(f"<b>{label}</b> nao pode ser zero.")
    return errors
 
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
 
def get_logo_b64() -> str:
    try:
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""
 
def show_contract_preview(docx_bytes: bytes):
    import mammoth, io
    with st.spinner("Gerando pre-visualizacao..."):
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
    st.markdown(f"""
    <div style="background:#fff;padding:60px 80px;max-width:860px;margin:0 auto;
        font-family:'DM Sans',sans-serif;font-size:14px;line-height:1.7;color:#111;
        border:1px solid #2a3a5c;border-radius:16px;box-shadow:0 8px 40px rgba(0,0,0,0.3);">
        {result.value}
    </div>""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
 
st.set_page_config(
    page_title="Arena Ice — Contratos",
    page_icon="⛸️",
    layout="wide",
)
 
LOGO_B64 = get_logo_b64()
 
# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Sora:wght@300;400;600;700;800&display=swap');
 
/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
 
.stApp {
    background: linear-gradient(135deg, #060d1f 0%, #0b1a3a 50%, #071228 100%);
    min-height: 100vh;
}
 
/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; padding-bottom: 4rem !important; }
 
/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07122b 0%, #0a1a3d 100%) !important;
    border-right: 1px solid rgba(96,165,250,0.15) !important;
}
[data-testid="stSidebar"] * { color: #a8c4f0 !important; }
 
/* ── Typography ── */
h1, h2, h3 { font-family: 'Sora', sans-serif !important; }
 
/* ── Form labels & text ── */
label, .stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label,
.stTimeInput label, .stTextArea label {
    color: #7bafd4 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
 
/* ── Inputs ── */
.stTextInput input, .stNumberInput input,
.stTextArea textarea, .stSelectbox select,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(96,165,250,0.2) !important;
    border-radius: 10px !important;
    color: #e8f0fe !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput input:focus, .stNumberInput input:focus,
.stTextArea textarea:focus,
[data-baseweb="input"] input:focus {
    border-color: rgba(96,165,250,0.6) !important;
    box-shadow: 0 0 0 3px rgba(96,165,250,0.12) !important;
}
 
/* ── Selectbox ── */
[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(96,165,250,0.2) !important;
    border-radius: 10px !important;
    color: #e8f0fe !important;
}
 
/* ── Date & time inputs ── */
[data-baseweb="base-input"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 10px !important;
}
 
/* ── Primary buttons ── */
.stButton button[kind="primary"],
.stFormSubmitButton button[kind="primary"] {
    background: linear-gradient(135deg, #1d6aff 0%, #0d4fd4 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 20px rgba(29,106,255,0.35) !important;
}
.stButton button[kind="primary"]:hover,
.stFormSubmitButton button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(29,106,255,0.5) !important;
}
 
/* ── Secondary buttons ── */
.stButton button[kind="secondary"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(96,165,250,0.25) !important;
    border-radius: 10px !important;
    color: #a8c4f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton button[kind="secondary"]:hover {
    background: rgba(96,165,250,0.1) !important;
    border-color: rgba(96,165,250,0.5) !important;
    color: #e8f0fe !important;
}
 
/* ── Download button ── */
.stDownloadButton button {
    background: linear-gradient(135deg, #0ea86e 0%, #0b8f5c 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 20px rgba(14,168,110,0.35) !important;
    transition: all 0.2s !important;
}
.stDownloadButton button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(14,168,110,0.5) !important;
}
 
/* ── Alerts ── */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}
 
/* ── Divider ── */
hr { border-color: rgba(96,165,250,0.12) !important; }
 
/* ── Caption / small text ── */
.stCaption, small { color: #4a6a9a !important; }
 
/* ── Spinner ── */
.stSpinner > div { border-top-color: #1d6aff !important; }
 
/* ── Section card ── */
.section-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(96,165,250,0.1);
    border-radius: 16px;
    padding: 24px 28px 8px 28px;
    margin-bottom: 20px;
}
.section-label {
    font-family: 'Sora', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4a7aaa;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label span {
    display: inline-block;
    width: 18px; height: 18px;
    background: rgba(29,106,255,0.15);
    border: 1px solid rgba(29,106,255,0.3);
    border-radius: 5px;
    text-align: center;
    line-height: 18px;
    font-size: 0.65rem;
}
</style>
""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
 
with st.sidebar:
    if LOGO_B64:
        st.markdown(f"""
        <div style="text-align:center;padding:24px 16px 16px;">
            <img src="data:image/png;base64,{LOGO_B64}"
                 style="max-width:140px;width:100%;opacity:0.95;"/>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:24px 16px 16px;">
            <span style="font-family:'Sora',sans-serif;font-size:1.1rem;
                font-weight:700;color:#a8c4f0;letter-spacing:0.05em;">
                ⛸️ ARENA ICE
            </span>
        </div>""", unsafe_allow_html=True)
 
    st.markdown('<hr style="border-color:rgba(96,165,250,0.15);margin:0 0 20px;"/>', unsafe_allow_html=True)
 
    st.markdown("""
    <p style="font-size:0.7rem;font-weight:600;letter-spacing:0.12em;
        text-transform:uppercase;color:#3a5a8a;margin:0 0 12px;padding:0 4px;">
        Sistema de Contratos
    </p>""", unsafe_allow_html=True)
 
    if st.button("🚪  Sair da sessao", use_container_width=True):
        st.session_state.clear()
        st.rerun()
 
 
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
            st.markdown(f"""
            <div style="text-align:center;margin-bottom:32px;">
                <img src="data:image/png;base64,{LOGO_B64}"
                     style="max-width:180px;width:100%;"/>
            </div>""", unsafe_allow_html=True)
 
        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(96,165,250,0.15);
            border-radius: 20px;
            padding: 40px 36px 32px;
            backdrop-filter: blur(12px);
        ">
            <p style="font-family:'Sora',sans-serif;font-size:1.4rem;font-weight:700;
                color:#e8f0fe;text-align:center;margin:0 0 6px;">
                Bem-vindo
            </p>
            <p style="font-size:0.85rem;color:#4a6a9a;text-align:center;margin:0 0 28px;">
                Acesso restrito — equipe Arena Ice
            </p>
        </div>
        """, unsafe_allow_html=True)
 
        password = st.text_input("Senha de acesso", type="password", placeholder="••••••••",
                                  label_visibility="collapsed")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Entrar", use_container_width=True, type="primary"):
            if password == "2031":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta. Tente novamente.")
 
    st.stop()
 
 
# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
 
for key, default in [
    ("contract_type", None),
    ("confirm_voltar", False),
    ("generated_docx", None),
    ("generated_filename", None),
    ("show_preview", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default
 
 
# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────
 
st.markdown("""
<div style="margin-bottom:8px;">
    <p style="font-family:'Sora',sans-serif;font-size:1.75rem;font-weight:800;
        color:#e8f0fe;margin:0;letter-spacing:-0.01em;">
        Gerador de Contratos
    </p>
    <p style="font-size:0.85rem;color:#3a5a8a;margin:4px 0 0;">
        Arena Ice — Sistema interno
    </p>
</div>
""", unsafe_allow_html=True)
 
st.markdown('<hr style="border-color:rgba(96,165,250,0.1);margin:16px 0 24px;"/>', unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# CONTRACT TYPE SELECTION
# ─────────────────────────────────────────────
 
if st.session_state.contract_type is None:
    st.session_state.confirm_voltar = False
    st.session_state.generated_docx = None
    st.session_state.generated_filename = None
    st.session_state.show_preview = False
 
    st.markdown("""
    <p style="font-family:'Sora',sans-serif;font-size:0.7rem;font-weight:700;
        letter-spacing:0.14em;text-transform:uppercase;color:#3a5a8a;margin-bottom:20px;">
        Selecione o tipo de contrato
    </p>""", unsafe_allow_html=True)
 
    col1, col2 = st.columns(2, gap="large")
 
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, rgba(29,106,255,0.08) 0%, rgba(29,106,255,0.03) 100%);
            border: 1px solid rgba(29,106,255,0.25);
            border-radius: 20px;
            padding: 36px 32px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        ">
            <div style="font-size:2.4rem;margin-bottom:14px;">🎉</div>
            <p style="font-family:'Sora',sans-serif;font-size:1.1rem;font-weight:700;
                color:#e8f0fe;margin:0 0 8px;">Evento Grande</p>
            <p style="font-size:0.82rem;color:#4a6a9a;margin:0;line-height:1.5;">
                Eventos completos, aniversarios<br/>grandes e reservas exclusivas.
            </p>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Selecionar  →", key="btn_big", use_container_width=True, type="primary"):
            st.session_state.contract_type = "big"
            st.rerun()
 
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, rgba(255,100,180,0.08) 0%, rgba(255,100,180,0.03) 100%);
            border: 1px solid rgba(255,100,180,0.25);
            border-radius: 20px;
            padding: 36px 32px;
            text-align: center;
        ">
            <div style="font-size:2.4rem;margin-bottom:14px;">🎂</div>
            <p style="font-family:'Sora',sans-serif;font-size:1.1rem;font-weight:700;
                color:#e8f0fe;margin:0 0 8px;">Pocket Event</p>
            <p style="font-size:0.82rem;color:#4a6a9a;margin:0;line-height:1.5;">
                Eventos menores e aniversarios<br/>rapidos com menos variaveis.
            </p>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Selecionar  →", key="btn_pocket", use_container_width=True, type="primary"):
            st.session_state.contract_type = "pocket"
            st.rerun()
 
    st.stop()
 
 
# ─────────────────────────────────────────────
# SUCCESS STATE
# ─────────────────────────────────────────────
 
if st.session_state.generated_docx is not None:
    docx_bytes = st.session_state.generated_docx
    filename   = st.session_state.generated_filename
    name_display = (
        filename.replace("contrato_", "")
                .replace(".docx", "")
                .replace("_", " ")
    )
 
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(14,168,110,0.1), rgba(14,168,110,0.04));
        border: 1px solid rgba(14,168,110,0.3);
        border-radius: 20px;
        padding: 36px 40px;
        text-align: center;
        margin-bottom: 28px;
    ">
        <div style="font-size:2.8rem;margin-bottom:12px;">✅</div>
        <p style="font-family:'Sora',sans-serif;font-size:1.3rem;font-weight:700;
            color:#e8f0fe;margin:0 0 6px;">Contrato gerado!</p>
        <p style="font-size:0.9rem;color:#4a9a7a;margin:0;">{name_display}</p>
    </div>""", unsafe_allow_html=True)
 
    col_dl, col_prev, col_new = st.columns(3, gap="medium")
 
    with col_dl:
        st.download_button(
            label="📄  Baixar contrato",
            data=docx_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with col_prev:
        preview_label = "🙈  Fechar preview" if st.session_state.show_preview else "👁  Pre-visualizar"
        if st.button(preview_label, use_container_width=True):
            st.session_state.show_preview = not st.session_state.show_preview
            st.rerun()
    with col_new:
        if st.button("📝  Novo contrato", use_container_width=True):
            st.session_state.generated_docx = None
            st.session_state.generated_filename = None
            st.session_state.show_preview = False
            st.session_state.contract_type = None
            st.rerun()
 
    if st.session_state.show_preview:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        show_contract_preview(docx_bytes)
 
    st.stop()
 
 
# ─────────────────────────────────────────────
# BACK BUTTON + BREADCRUMB
# ─────────────────────────────────────────────
 
type_label = "Evento Grande" if st.session_state.contract_type == "big" else "Pocket Event"
type_icon  = "🎉" if st.session_state.contract_type == "big" else "🎂"
 
col_back, col_crumb = st.columns([1, 5])
 
with col_back:
    if not st.session_state.confirm_voltar:
        if st.button("← Voltar"):
            st.session_state.confirm_voltar = True
            st.rerun()
    else:
        st.markdown("""
        <p style="font-size:0.8rem;color:#e8c060;margin-bottom:6px;">
            Perder os dados preenchidos?
        </p>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sim", use_container_width=True):
                st.session_state.contract_type = None
                st.session_state.confirm_voltar = False
                st.rerun()
        with c2:
            if st.button("Nao", use_container_width=True):
                st.session_state.confirm_voltar = False
                st.rerun()
 
with col_crumb:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;padding-top:6px;">
        <span style="font-size:0.75rem;color:#3a5a8a;">Contratos</span>
        <span style="font-size:0.75rem;color:#2a3a5c;">›</span>
        <span style="font-size:0.75rem;font-weight:600;color:#7bafd4;">
            {type_icon} {type_label}
        </span>
    </div>""", unsafe_allow_html=True)
 
st.markdown('<hr style="border-color:rgba(96,165,250,0.1);margin:16px 0 28px;"/>', unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# SECTION CARD HELPER
# ─────────────────────────────────────────────
 
def section(icon: str, label: str):
    st.markdown(f"""
    <div class="section-label">
        <span>{icon}</span> {label}
    </div>""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────
# BIG EVENT CONTRACT
# ─────────────────────────────────────────────
 
if st.session_state.contract_type == "big":
 
    st.markdown("""
    <p style="font-family:'Sora',sans-serif;font-size:1.3rem;font-weight:700;
        color:#e8f0fe;margin:0 0 24px;">
        🎉 Contrato — Evento Grande
    </p>""", unsafe_allow_html=True)
 
    with st.form("big_contract"):
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("👤", "Dados do Contratante")
        col1, col2, col3 = st.columns(3)
        with col1:
            contractor_name = st.text_input("Nome do contratante *", placeholder="Ex: Joao Silva")
        with col2:
            contractor_cpf = st.text_input("CPF *", placeholder="Ex: 123.456.789-00")
        with col3:
            contractor_birthdate_raw = st.date_input("Data de nascimento *", value=None,
                min_value=date(1920,1,1), max_value=date.today(), format="DD/MM/YYYY")
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("📅", "Informacoes do Evento")
        col4, col5 = st.columns(2)
        with col4:
            event_name = st.text_input("Nome do evento *", value="ANIVERSARIO",
                placeholder="Ex: Aniversario da Maria")
        with col5:
            event_date_raw = st.date_input("Data do evento *", value=None,
                min_value=date.today(), format="DD/MM/YYYY")
        col7, col8, col9 = st.columns(3)
        with col7:
            event_duration_hours = st.text_input("Duracao (horas) *", placeholder="Ex: 3")
        with col8:
            event_start_time = st.time_input("Horario inicio *", value=None, step=1800)
        with col9:
            event_end_time = st.time_input("Horario termino *", value=None, step=1800)
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("👥", "Capacidade")
        col10, col11 = st.columns(2)
        with col10:
            guest_count = st.number_input("Maximo de convidados *", min_value=0,
                value=None, step=1, placeholder="Ex: 50")
        with col11:
            skaters_count = st.number_input("Pessoas para patinar *", min_value=0,
                value=None, step=1, placeholder="Ex: 20")
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("🎯", "Programacao")
        col12, col13, col14 = st.columns(3)
        with col12:
            first  = st.text_input("1 atividade *", placeholder="Ex: 14:30 - Entrada na pista")
        with col13:
            second = st.text_input("2 atividade *", placeholder="Ex: 15:30 - Corte do bolo")
        with col14:
            third  = st.text_input("3 atividade *", placeholder="Ex: 16:30 - Encerramento")
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("🏟️", "Arena")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            rink_name   = st.text_input("Nome da pista *", placeholder="Ex: Arena Ice Brasil")
        with col_a2:
            tipo_espaco = st.selectbox("Tipo de espaco", ["Espaco exclusivo", "Arena compartilhada"])
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("💰", "Valores e Pagamento")
        contract_total_value = st.number_input("Valor total do contrato (R$) *",
            min_value=0.0, value=None, step=100.0, format="%.2f", placeholder="Ex: 1500.00")
        payment_terms = st.text_area("Condicoes de pagamento *",
            placeholder="Ex: 50% via PIX na assinatura e 50% ate 3 dias antes do evento.",
            height=90)
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("✍️", "Assinatura")
        col15, col16 = st.columns(2)
        with col15:
            signature_day   = st.text_input("Dia *", placeholder="Ex: 12")
        with col16:
            signature_month = st.text_input("Mes *", placeholder="Ex: Maio")
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.caption("* Campos obrigatorios")
        submit = st.form_submit_button("Gerar contrato  →", type="primary", use_container_width=True)
 
    if submit:
        contractor_birthdate  = contractor_birthdate_raw.strftime("%d/%m/%Y") if contractor_birthdate_raw else ""
        event_date            = event_date_raw.strftime("%d/%m/%Y") if event_date_raw else ""
        event_weekday         = WEEKDAYS_PT[event_date_raw.weekday()] if event_date_raw else ""
        event_start_time_str  = event_start_time.strftime("%H:%M") if event_start_time else ""
        event_end_time_str    = event_end_time.strftime("%H:%M") if event_end_time else ""
 
        errors = validate_fields({
            "Nome do contratante": contractor_name,
            "CPF": contractor_cpf,
            "Data de nascimento": contractor_birthdate,
            "Nome do evento": event_name,
            "Data do evento": event_date,
            "Duracao (horas)": event_duration_hours,
            "Horario inicio": event_start_time_str,
            "Horario termino": event_end_time_str,
            "Maximo de convidados": guest_count or 0,
            "Pessoas para patinar": skaters_count or 0,
            "1 atividade": first, "2 atividade": second, "3 atividade": third,
            "Nome da pista": rink_name,
            "Valor total do contrato": contract_total_value or 0.0,
            "Condicoes de pagamento": payment_terms,
            "Dia de assinatura": signature_day,
            "Mes de assinatura": signature_month,
        })
 
        if contractor_cpf and not validate_cpf_format(contractor_cpf):
            errors.append("<b>CPF</b> deve estar no formato 123.456.789-00.")
        if event_start_time and event_end_time and event_end_time <= event_start_time:
            errors.append("<b>Horario termino</b> deve ser depois do horario de inicio.")
 
        if errors:
            err_html = "".join(f"<li>{e}</li>" for e in errors)
            st.markdown(f"""
            <div style="background:rgba(255,80,80,0.08);border:1px solid rgba(255,80,80,0.25);
                border-radius:12px;padding:16px 20px;margin-top:12px;">
                <p style="color:#ff8080;font-weight:600;margin:0 0 8px;font-size:0.85rem;">
                    Corrija os campos abaixo:
                </p>
                <ul style="color:#cc6060;font-size:0.82rem;margin:0;padding-left:18px;">
                    {err_html}
                </ul>
            </div>""", unsafe_allow_html=True)
        else:
            try:
                context = {
                    "contractor_name": contractor_name, "contractor_cpf": contractor_cpf,
                    "contractor_birthdate": contractor_birthdate, "event_name": event_name,
                    "event_date": event_date, "event_weekday": event_weekday,
                    "event_duration_hours": event_duration_hours,
                    "event_start_time": event_start_time_str, "event_end_time": event_end_time_str,
                    "guest_count": int(guest_count), "skaters_count": int(skaters_count),
                    "rink_name": rink_name, "tipo_espaco": tipo_espaco,
                    "contract_total_value": format_brl(contract_total_value),
                    "payment_terms": payment_terms, "signature_day": signature_day,
                    "signature_month": signature_month,
                    "first": first, "second": second, "third": third,
                }
                safe_name = contractor_name.strip().replace(" ", "_")
                safe_date = event_date.replace("/", "-")
                st.session_state.generated_docx     = render_docx(BIG_TEMPLATE, context)
                st.session_state.generated_filename  = f"contrato_{safe_name}_{safe_date}.docx"
                st.session_state.show_preview        = False
                st.rerun()
            except FileNotFoundError:
                st.error("Template nao encontrado. Contate o administrador.")
 
 
# ─────────────────────────────────────────────
# POCKET EVENT CONTRACT
# ─────────────────────────────────────────────
 
elif st.session_state.contract_type == "pocket":
 
    st.markdown("""
    <p style="font-family:'Sora',sans-serif;font-size:1.3rem;font-weight:700;
        color:#e8f0fe;margin:0 0 24px;">
        🎂 Contrato — Pocket Event
    </p>""", unsafe_allow_html=True)
 
    with st.form("pocket_contract"):
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("👤", "Dados do Contratante")
        col1, col2 = st.columns(2)
        with col1:
            contractor_name = st.text_input("Nome do contratante *", placeholder="Ex: Joao Silva")
        with col2:
            contractor_cpf = st.text_input("CPF *", placeholder="Ex: 123.456.789-00")
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("🎉", "Aniversario")
        col3, col4 = st.columns(2)
        with col3:
            birthday_person = st.text_input("Nome do aniversariante *", placeholder="Ex: Maria")
        with col4:
            birthday_age = st.number_input("Idade *", min_value=0, value=None,
                step=1, placeholder="Ex: 7")
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("📅", "Evento")
        col5, col6, col7 = st.columns(3)
        with col5:
            event_date_raw = st.date_input("Data do evento *", value=None,
                min_value=date.today(), format="DD/MM/YYYY")
        with col6:
            start_time = st.time_input("Horario inicio *", value=None, step=1800)
        with col7:
            end_time = st.time_input("Horario termino *", value=None, step=1800)
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        section("💰", "Pagamento")
        col8, col9, col10 = st.columns(3)
        with col8:
            contract_value = st.number_input("Valor do contrato (R$) *", min_value=0.0,
                value=None, step=50.0, format="%.2f", placeholder="Ex: 800.00")
        with col9:
            payment_method = st.selectbox("Forma de pagamento *",
                ["PIX", "Cartao de credito", "Cartao de debito", "Boleto", "Dinheiro", "Outro"])
        with col10:
            payment_date_raw = st.date_input("Data de pagamento *", value=None,
                min_value=date.today(), format="DD/MM/YYYY")
        st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.caption("* Campos obrigatorios")
        submit = st.form_submit_button("Gerar contrato  →", type="primary", use_container_width=True)
 
    if submit:
        event_date    = event_date_raw.strftime("%d/%m/%Y") if event_date_raw else ""
        start_time_str = start_time.strftime("%H:%M") if start_time else ""
        end_time_str   = end_time.strftime("%H:%M") if end_time else ""
        payment_date   = payment_date_raw.strftime("%d/%m/%Y") if payment_date_raw else ""
 
        errors = validate_fields({
            "Nome do contratante": contractor_name, "CPF": contractor_cpf,
            "Nome do aniversariante": birthday_person, "Idade": birthday_age or 0,
            "Data do evento": event_date, "Horario inicio": start_time_str,
            "Horario termino": end_time_str, "Valor do contrato": contract_value or 0.0,
            "Data de pagamento": payment_date,
        })
 
        if contractor_cpf and not validate_cpf_format(contractor_cpf):
            errors.append("<b>CPF</b> deve estar no formato 123.456.789-00.")
        if start_time and end_time and end_time <= start_time:
            errors.append("<b>Horario termino</b> deve ser depois do horario de inicio.")
 
        if errors:
            err_html = "".join(f"<li>{e}</li>" for e in errors)
            st.markdown(f"""
            <div style="background:rgba(255,80,80,0.08);border:1px solid rgba(255,80,80,0.25);
                border-radius:12px;padding:16px 20px;margin-top:12px;">
                <p style="color:#ff8080;font-weight:600;margin:0 0 8px;font-size:0.85rem;">
                    Corrija os campos abaixo:
                </p>
                <ul style="color:#cc6060;font-size:0.82rem;margin:0;padding-left:18px;">
                    {err_html}
                </ul>
            </div>""", unsafe_allow_html=True)
        else:
            try:
                context = {
                    "contractor_name": contractor_name, "contractor_cpf": contractor_cpf,
                    "birthday_person": birthday_person, "birthday_age": int(birthday_age),
                    "event_date": event_date, "start_time": start_time_str,
                    "end_time": end_time_str, "contract_value": format_brl(contract_value),
                    "payment_method": payment_method, "payment_date": payment_date,
                }
                safe_name = contractor_name.strip().replace(" ", "_")
                safe_date = event_date.replace("/", "-")
                st.session_state.generated_docx    = render_docx(POCKET_TEMPLATE, context)
                st.session_state.generated_filename = f"contrato_{safe_name}_{safe_date}.docx"
                st.session_state.show_preview       = False
                st.rerun()
            except FileNotFoundError:
                st.error("Template nao encontrado. Contate o administrador.")
 