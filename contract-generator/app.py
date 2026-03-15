import re
import os
import base64
import subprocess
import tempfile
from datetime import date
 
import streamlit as st
from docxtpl import DocxTemplate
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
BIG_TEMPLATE = os.path.join(BASE_DIR, "contract_template.docx")
POCKET_TEMPLATE = os.path.join(BASE_DIR, "pocket_template.docx")
 
WEEKDAYS_PT = {
    0: "Segunda-feira",
    1: "Terca-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sabado",
    6: "Domingo",
}
 
CPF_PATTERN = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
 
 
# ---------------------------------------------
# HELPERS
# ---------------------------------------------
 
def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
 
 
def validate_cpf_format(cpf: str) -> bool:
    return bool(CPF_PATTERN.match(cpf.strip()))
 
 
def validate_fields(fields: dict) -> list:
    errors = []
    for label, value in fields.items():
        if isinstance(value, str) and not value.strip():
            errors.append(f"**{label}** e obrigatorio.")
        elif isinstance(value, (int, float)) and value == 0:
            errors.append(f"**{label}** nao pode ser zero.")
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
 
 
def docx_to_pdf_base64(docx_bytes: bytes):
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = os.path.join(tmpdir, "contract.docx")
        pdf_path = os.path.join(tmpdir, "contract.pdf")
        with open(docx_path, "wb") as f:
            f.write(docx_bytes)
        result = subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", tmpdir, docx_path],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0 or not os.path.exists(pdf_path):
            return None
        with open(pdf_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
 
 
def show_contract_preview(docx_bytes: bytes):
    with st.spinner("Gerando pre-visualizacao..."):
        pdf_b64 = docx_to_pdf_base64(docx_bytes)
    if pdf_b64 is None:
        st.error("Nao foi possivel gerar a pre-visualizacao. Verifique se o LibreOffice esta instalado.")
        return
    pdf_embed = f"""
        <iframe
            src="data:application/pdf;base64,{pdf_b64}"
            width="100%"
            height="900px"
            style="border: 1px solid #ddd; border-radius: 8px;"
        ></iframe>
    """
    st.markdown(pdf_embed, unsafe_allow_html=True)
 
 
# ---------------------------------------------
# PAGE CONFIG
# ---------------------------------------------
 
st.set_page_config(
    page_title="Arena Ice Contract Generator",
    page_icon="⛸️",
    layout="wide",
)
 
# ---------------------------------------------
# SIDEBAR
# ---------------------------------------------
 
with st.sidebar:
    st.markdown("## ⛸️ Arena Ice")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()
 
st.title("⛸️ Arena Ice Contract Generator")
 
# ---------------------------------------------
# PASSWORD GATE
# ---------------------------------------------
 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
 
if not st.session_state.authenticated:
    st.markdown("### 🔒 Acesso restrito")
    password = st.text_input("Digite a senha para continuar:", type="password")
    if password == "2031":
        st.session_state.authenticated = True
        st.rerun()
    elif password:
        st.error("Senha incorreta.")
    st.stop()
 
# ---------------------------------------------
# SESSION STATE INIT
# ---------------------------------------------
 
if "contract_type" not in st.session_state:
    st.session_state.contract_type = None
if "confirm_voltar" not in st.session_state:
    st.session_state.confirm_voltar = False
if "generated_docx" not in st.session_state:
    st.session_state.generated_docx = None
if "generated_filename" not in st.session_state:
    st.session_state.generated_filename = None
if "show_preview" not in st.session_state:
    st.session_state.show_preview = False
 
# ---------------------------------------------
# CONTRACT TYPE SELECTION
# ---------------------------------------------
 
if st.session_state.contract_type is None:
    st.session_state.confirm_voltar = False
    st.session_state.generated_docx = None
    st.session_state.generated_filename = None
    st.session_state.show_preview = False
 
    st.markdown("### Selecione o tipo de contrato para comecar")
    st.write("")
 
    col1, col2 = st.columns(2)
 
    with col1:
        st.markdown(
            """
            <div style="
                border: 2px solid #1E90FF;
                border-radius: 12px;
                padding: 24px;
                text-align: center;
                background: linear-gradient(135deg, #e8f4ff, #f0f8ff);
                min-height: 140px;
            ">
                <h2 style="color:#1E90FF; margin:0;">🎉</h2>
                <h3 style="color:#1E90FF; margin:8px 0;">Evento Grande</h3>
                <p style="color:#444; font-size:14px;">Eventos completos, aniversarios grandes e reservas exclusivas da pista.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Selecionar Evento Grande", use_container_width=True, type="primary"):
            st.session_state.contract_type = "big"
            st.rerun()
 
    with col2:
        st.markdown(
            """
            <div style="
                border: 2px solid #FF69B4;
                border-radius: 12px;
                padding: 24px;
                text-align: center;
                background: linear-gradient(135deg, #fff0f8, #fff5fb);
                min-height: 140px;
            ">
                <h2 style="color:#FF69B4; margin:0;">🎂</h2>
                <h3 style="color:#FF69B4; margin:8px 0;">Pocket Event</h3>
                <p style="color:#444; font-size:14px;">Eventos menores e aniversarios rapidos com menos variaveis.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Selecionar Pocket Event", use_container_width=True, type="primary"):
            st.session_state.contract_type = "pocket"
            st.rerun()
 
    st.stop()
 
# ---------------------------------------------
# SUCCESS STATE
# ---------------------------------------------
 
if st.session_state.generated_docx is not None:
    docx_bytes = st.session_state.generated_docx
    filename = st.session_state.generated_filename
    name_display = filename.replace("contrato_", "").replace(".docx", "").replace("_", " ")
 
    st.success(f"✅ Contrato gerado para **{name_display}**")
    st.write("")
 
    col_dl, col_prev, col_new = st.columns([2, 2, 2])
 
    with col_dl:
        st.download_button(
            label="📄 Baixar contrato",
            data=docx_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            type="primary",
        )
 
    with col_prev:
        preview_label = "🙈 Fechar pre-visualizacao" if st.session_state.show_preview else "👁 Pre-visualizar contrato"
        if st.button(preview_label, use_container_width=True):
            st.session_state.show_preview = not st.session_state.show_preview
            st.rerun()
 
    with col_new:
        if st.button("📝 Novo contrato", use_container_width=True):
            st.session_state.generated_docx = None
            st.session_state.generated_filename = None
            st.session_state.show_preview = False
            st.session_state.contract_type = None
            st.rerun()
 
    if st.session_state.show_preview:
        st.divider()
        show_contract_preview(docx_bytes)
 
    st.stop()
 
# ---------------------------------------------
# BACK BUTTON WITH CONFIRMATION
# ---------------------------------------------
 
type_label = "🎉 Evento Grande" if st.session_state.contract_type == "big" else "🎂 Pocket Event"
col_back, col_label = st.columns([2, 5])
 
with col_back:
    if not st.session_state.confirm_voltar:
        if st.button("← Voltar"):
            st.session_state.confirm_voltar = True
            st.rerun()
    else:
        st.warning("Perder os dados preenchidos?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sim", use_container_width=True):
                st.session_state.contract_type = None
                st.session_state.confirm_voltar = False
                st.rerun()
        with c2:
            if st.button("❌ Nao", use_container_width=True):
                st.session_state.confirm_voltar = False
                st.rerun()
 
with col_label:
    st.markdown(f"**Tipo selecionado:** {type_label}")
 
st.divider()
 
# ---------------------------------------------
# BIG EVENT CONTRACT
# ---------------------------------------------
 
if st.session_state.contract_type == "big":
 
    st.header("🎉 Contrato de Evento Grande")
 
    with st.form("big_contract"):
 
        st.subheader("👤 Dados do Contratante")
        col1, col2, col3 = st.columns(3)
        with col1:
            contractor_name = st.text_input("Nome do contratante *", placeholder="Ex: Joao Silva")
        with col2:
            contractor_cpf = st.text_input("CPF *", placeholder="Ex: 123.456.789-00")
        with col3:
            contractor_birthdate_raw = st.date_input(
                "Data de nascimento *", value=None,
                min_value=date(1920, 1, 1), max_value=date.today(), format="DD/MM/YYYY"
            )
 
        st.subheader("📅 Informacoes do Evento")
        col4, col5 = st.columns(2)
        with col4:
            event_name = st.text_input("Nome do evento *", value="ANIVERSARIO", placeholder="Ex: Aniversario da Maria")
        with col5:
            event_date_raw = st.date_input("Data do evento *", value=None, min_value=date.today(), format="DD/MM/YYYY")
 
        col7, col8, col9 = st.columns(3)
        with col7:
            event_duration_hours = st.text_input("Duracao (horas) *", placeholder="Ex: 3")
        with col8:
            event_start_time = st.time_input("Horario inicio *", value=None, step=1800)
        with col9:
            event_end_time = st.time_input("Horario termino *", value=None, step=1800)
 
        st.subheader("👥 Capacidade")
        col10, col11 = st.columns(2)
        with col10:
            guest_count = st.number_input("Maximo de convidados *", min_value=0, value=None, step=1, placeholder="Ex: 50")
        with col11:
            skaters_count = st.number_input("Pessoas para patinar *", min_value=0, value=None, step=1, placeholder="Ex: 20")
 
        st.subheader("🎯 Programacao")
        col12, col13, col14 = st.columns(3)
        with col12:
            first = st.text_input("1 atividade *", placeholder="Ex: 14:30 - Entrada na pista")
        with col13:
            second = st.text_input("2 atividade *", placeholder="Ex: 15:30 - Corte do bolo")
        with col14:
            third = st.text_input("3 atividade *", placeholder="Ex: 16:30 - Encerramento")
 
        st.subheader("🏟️ Arena")
        col_arena1, col_arena2 = st.columns(2)
        with col_arena1:
            rink_name = st.text_input("Nome da pista *", placeholder="Ex: Arena Ice Brasil")
        with col_arena2:
            tipo_espaco = st.selectbox("Tipo de espaco", ["Espaco exclusivo", "Arena compartilhada"])
 
        st.subheader("💰 Valores")
        contract_total_value = st.number_input(
            "Valor total do contrato (R$) *", min_value=0.0, value=None, step=100.0, format="%.2f", placeholder="Ex: 1500.00"
        )
        payment_terms = st.text_area(
            "Condicoes de pagamento *",
            placeholder="Ex: 50% via PIX na assinatura e 50% ate 3 dias antes do evento.",
            height=100,
        )
 
        st.subheader("✍️ Assinatura")
        col15, col16 = st.columns(2)
        with col15:
            signature_day = st.text_input("Dia *", placeholder="Ex: 12")
        with col16:
            signature_month = st.text_input("Mes *", placeholder="Ex: Maio")
 
        st.caption("* Campos obrigatorios")
        submit = st.form_submit_button("Gerar contrato", type="primary", use_container_width=True)
 
    if submit:
        contractor_birthdate = contractor_birthdate_raw.strftime("%d/%m/%Y") if contractor_birthdate_raw else ""
        event_date = event_date_raw.strftime("%d/%m/%Y") if event_date_raw else ""
        event_weekday = WEEKDAYS_PT[event_date_raw.weekday()] if event_date_raw else ""
        event_start_time_str = event_start_time.strftime("%H:%M") if event_start_time else ""
        event_end_time_str = event_end_time.strftime("%H:%M") if event_end_time else ""
 
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
            "1 atividade": first,
            "2 atividade": second,
            "3 atividade": third,
            "Nome da pista": rink_name,
            "Valor total do contrato": contract_total_value or 0.0,
            "Condicoes de pagamento": payment_terms,
            "Dia de assinatura": signature_day,
            "Mes de assinatura": signature_month,
        })
 
        if contractor_cpf and not validate_cpf_format(contractor_cpf):
            errors.append("**CPF** deve estar no formato 123.456.789-00.")
        if event_start_time and event_end_time and event_end_time <= event_start_time:
            errors.append("**Horario termino** deve ser depois do horario de inicio.")
 
        if errors:
            st.error("Por favor, corrija os seguintes campos antes de continuar:")
            for e in errors:
                st.markdown(f"- {e}")
        else:
            try:
                context = {
                    "contractor_name": contractor_name,
                    "contractor_cpf": contractor_cpf,
                    "contractor_birthdate": contractor_birthdate,
                    "event_name": event_name,
                    "event_date": event_date,
                    "event_weekday": event_weekday,
                    "event_duration_hours": event_duration_hours,
                    "event_start_time": event_start_time_str,
                    "event_end_time": event_end_time_str,
                    "guest_count": int(guest_count),
                    "skaters_count": int(skaters_count),
                    "rink_name": rink_name,
                    "tipo_espaco": tipo_espaco,
                    "contract_total_value": format_brl(contract_total_value),
                    "payment_terms": payment_terms,
                    "signature_day": signature_day,
                    "signature_month": signature_month,
                    "first": first,
                    "second": second,
                    "third": third,
                }
                safe_name = contractor_name.strip().replace(" ", "_")
                safe_date = event_date.replace("/", "-")
                filename = f"contrato_{safe_name}_{safe_date}.docx"
                st.session_state.generated_docx = render_docx(BIG_TEMPLATE, context)
                st.session_state.generated_filename = filename
                st.session_state.show_preview = False
                st.rerun()
            except FileNotFoundError:
                st.error("Template nao encontrado. Contate o administrador.")
 
# ---------------------------------------------
# POCKET EVENT CONTRACT
# ---------------------------------------------
 
elif st.session_state.contract_type == "pocket":
 
    st.header("🎂 Contrato Pocket Event")
 
    with st.form("pocket_contract"):
 
        st.subheader("👤 Dados do Contratante")
        col1, col2 = st.columns(2)
        with col1:
            contractor_name = st.text_input("Nome do contratante *", placeholder="Ex: Joao Silva")
        with col2:
            contractor_cpf = st.text_input("CPF *", placeholder="Ex: 123.456.789-00")
 
        st.subheader("🎉 Aniversario")
        col3, col4 = st.columns(2)
        with col3:
            birthday_person = st.text_input("Nome do aniversariante *", placeholder="Ex: Maria")
        with col4:
            birthday_age = st.number_input("Idade *", min_value=0, value=None, step=1, placeholder="Ex: 7")
 
        st.subheader("📅 Evento")
        col5, col6, col7 = st.columns(3)
        with col5:
            event_date_raw = st.date_input("Data do evento *", value=None, min_value=date.today(), format="DD/MM/YYYY")
        with col6:
            start_time = st.time_input("Horario inicio *", value=None, step=1800)
        with col7:
            end_time = st.time_input("Horario termino *", value=None, step=1800)
 
        st.subheader("💰 Pagamento")
        col8, col9, col10 = st.columns(3)
        with col8:
            contract_value = st.number_input(
                "Valor do contrato (R$) *", min_value=0.0, value=None, step=50.0, format="%.2f", placeholder="Ex: 800.00"
            )
        with col9:
            payment_method = st.selectbox(
                "Forma de pagamento *",
                ["PIX", "Cartao de credito", "Cartao de debito", "Boleto", "Dinheiro", "Outro"],
            )
        with col10:
            payment_date_raw = st.date_input("Data de pagamento *", value=None, min_value=date.today(), format="DD/MM/YYYY")
 
        st.caption("* Campos obrigatorios")
        submit = st.form_submit_button("Gerar contrato", type="primary", use_container_width=True)
 
    if submit:
        event_date = event_date_raw.strftime("%d/%m/%Y") if event_date_raw else ""
        start_time_str = start_time.strftime("%H:%M") if start_time else ""
        end_time_str = end_time.strftime("%H:%M") if end_time else ""
        payment_date = payment_date_raw.strftime("%d/%m/%Y") if payment_date_raw else ""
 
        errors = validate_fields({
            "Nome do contratante": contractor_name,
            "CPF": contractor_cpf,
            "Nome do aniversariante": birthday_person,
            "Idade": birthday_age or 0,
            "Data do evento": event_date,
            "Horario inicio": start_time_str,
            "Horario termino": end_time_str,
            "Valor do contrato": contract_value or 0.0,
            "Data de pagamento": payment_date,
        })
 
        if contractor_cpf and not validate_cpf_format(contractor_cpf):
            errors.append("**CPF** deve estar no formato 123.456.789-00.")
        if start_time and end_time and end_time <= start_time:
            errors.append("**Horario termino** deve ser depois do horario de inicio.")
 
        if errors:
            st.error("Por favor, corrija os seguintes campos antes de continuar:")
            for e in errors:
                st.markdown(f"- {e}")
        else:
            try:
                context = {
                    "contractor_name": contractor_name,
                    "contractor_cpf": contractor_cpf,
                    "birthday_person": birthday_person,
                    "birthday_age": int(birthday_age),
                    "event_date": event_date,
                    "start_time": start_time_str,
                    "end_time": end_time_str,
                    "contract_value": format_brl(contract_value),
                    "payment_method": payment_method,
                    "payment_date": payment_date,
                }
                safe_name = contractor_name.strip().replace(" ", "_")
                safe_date = event_date.replace("/", "-")
                filename = f"contrato_{safe_name}_{safe_date}.docx"
                st.session_state.generated_docx = render_docx(POCKET_TEMPLATE, context)
                st.session_state.generated_filename = filename
                st.session_state.show_preview = False
                st.rerun()
            except FileNotFoundError:
                st.error("Template nao encontrado. Contate o administrador.")
 