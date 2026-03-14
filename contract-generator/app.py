import streamlit as st
from docxtpl import DocxTemplate
import tempfile
import os
from datetime import date, datetime

BASE_DIR = os.path.dirname(os.path.abspath(**file**))

BIG_TEMPLATE = os.path.join(BASE_DIR, “contract_template.docx”)
POCKET_TEMPLATE = os.path.join(BASE_DIR, “pocket_template.docx”)

WEEKDAYS_PT = {
0: “Segunda-feira”,
1: “Terça-feira”,
2: “Quarta-feira”,
3: “Quinta-feira”,
4: “Sexta-feira”,
5: “Sábado”,
6: “Domingo”,
}

def format_brl(value: float) -> str:
“”“Format a float as Brazilian Real currency string.”””
return f”R$ {value:,.2f}”.replace(”,”, “X”).replace(”.”, “,”).replace(“X”, “.”)

def render_and_download(template_path: str, context: dict, filename: str):
“”“Render a DocxTemplate with context and offer a download button.”””
try:
doc = DocxTemplate(template_path)
except FileNotFoundError:
st.error(“❌ Template não encontrado. Contate o administrador.”)
return

```
doc.render(context)

tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
try:
    doc.save(tmp.name)
    with open(tmp.name, "rb") as f:
        st.success("✅ Contrato gerado com sucesso!")
        st.download_button(
            label="📄 Baixar contrato",
            data=f,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
finally:
    os.unlink(tmp.name)
```

def validate_fields(fields: dict) -> list[str]:
“”“Return a list of error messages for any missing or zero required fields.”””
errors = []
for label, value in fields.items():
if isinstance(value, str) and not value.strip():
errors.append(f”**{label}** é obrigatório.”)
elif isinstance(value, (int, float)) and value == 0:
errors.append(f”**{label}** não pode ser zero.”)
return errors

# ─────────────────────────────────────────────

# PAGE CONFIG

# ─────────────────────────────────────────────

st.set_page_config(
page_title=“Arena Ice Contract Generator”,
page_icon=“⛸️”,
layout=“wide”,
)

st.title(“⛸️ Arena Ice Contract Generator”)

# ─────────────────────────────────────────────

# CONTRACT TYPE SELECTION

# ─────────────────────────────────────────────

if “contract_type” not in st.session_state:
st.session_state.contract_type = None

if st.session_state.contract_type is None:
st.markdown(”### Selecione o tipo de contrato para começar”)
st.write(””)

```
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
            <p style="color:#444; font-size:14px;">Eventos completos, aniversários grandes e reservas exclusivas da pista.</p>
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
            <p style="color:#444; font-size:14px;">Eventos menores e aniversários rápidos com menos variáveis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Selecionar Pocket Event", use_container_width=True, type="primary"):
        st.session_state.contract_type = "pocket"
        st.rerun()

st.stop()
```

# ─────────────────────────────────────────────

# BACK BUTTON (shown after selection)

# ─────────────────────────────────────────────

type_label = “🎉 Evento Grande” if st.session_state.contract_type == “big” else “🎂 Pocket Event”
col_back, col_label = st.columns([1, 6])

with col_back:
if st.button(“← Voltar”):
st.session_state.contract_type = None
st.rerun()

with col_label:
st.markdown(f”**Tipo selecionado:** {type_label}”)

st.divider()

# ─────────────────────────────────────────────

# BIG EVENT CONTRACT

# ─────────────────────────────────────────────

if st.session_state.contract_type == “big”:

```
st.header("🎉 Contrato de Evento Grande")

with st.form("big_contract"):

    st.subheader("👤 Dados do Contratante")

    col1, col2, col3 = st.columns(3)

    with col1:
        contractor_name = st.text_input(
            "Nome do contratante *",
            placeholder="Ex: João Silva",
        )
    with col2:
        contractor_cpf = st.text_input(
            "CPF *",
            placeholder="Ex: 123.456.789-00",
        )
    with col3:
        contractor_birthdate_raw = st.date_input(
            "Data de nascimento *",
            value=None,
            min_value=date(1920, 1, 1),
            max_value=date.today(),
            format="DD/MM/YYYY",
        )

    st.subheader("📅 Informações do Evento")

    col4, col5 = st.columns(2)

    with col4:
        event_name = st.text_input(
            "Nome do evento *",
            value="ANIVERSÁRIO",
            placeholder="Ex: Aniversário da Maria",
        )
    with col5:
        event_date_raw = st.date_input(
            "Data do evento *",
            value=None,
            min_value=date.today(),
            format="DD/MM/YYYY",
        )

    col7, col8, col9 = st.columns(3)

    with col7:
        event_duration_hours = st.text_input(
            "Duração (horas) *",
            placeholder="Ex: 3",
        )
    with col8:
        event_start_time = st.time_input("Horário início *", value=None, step=1800)
    with col9:
        event_end_time = st.time_input("Horário término *", value=None, step=1800)

    st.subheader("👥 Capacidade")

    col10, col11 = st.columns(2)

    with col10:
        guest_count = st.number_input(
            "Máximo de convidados *",
            min_value=0,
            value=None,
            step=1,
            placeholder="Ex: 50",
        )
    with col11:
        skaters_count = st.number_input(
            "Pessoas para patinar *",
            min_value=0,
            value=None,
            step=1,
            placeholder="Ex: 20",
        )

    st.subheader("🎯 Programação")

    col12, col13, col14 = st.columns(3)

    with col12:
        first = st.text_input(
            "1ª atividade *",
            placeholder="Ex: 14:30 - Entrada na pista",
        )
    with col13:
        second = st.text_input(
            "2ª atividade *",
            placeholder="Ex: 15:30 - Corte do bolo",
        )
    with col14:
        third = st.text_input(
            "3ª atividade *",
            placeholder="Ex: 16:30 - Encerramento",
        )

    st.subheader("🏟️ Arena")

    col_arena1, col_arena2 = st.columns(2)

    with col_arena1:
        rink_name = st.text_input(
            "Nome da pista *",
            placeholder="Ex: Arena Ice Brasil",
        )
    with col_arena2:
        tipo_espaco = st.selectbox(
            "Tipo de espaço",
            ["Espaço exclusivo", "Arena compartilhada"],
        )

    st.subheader("💰 Valores")

    contract_total_value = st.number_input(
        "Valor total do contrato (R$) *",
        min_value=0.0,
        value=None,
        step=100.0,
        format="%.2f",
        placeholder="Ex: 1500.00",
    )

    payment_terms = st.text_area(
        "Condições de pagamento *",
        placeholder="Ex: 50% via PIX na assinatura e 50% até 3 dias antes do evento.",
        height=100,
    )

    st.subheader("✍️ Assinatura")

    col15, col16 = st.columns(2)

    with col15:
        signature_day = st.text_input("Dia *", placeholder="Ex: 12")
    with col16:
        signature_month = st.text_input("Mês *", placeholder="Ex: Maio")

    st.caption("* Campos obrigatórios")
    submit = st.form_submit_button("Gerar contrato", type="primary", use_container_width=True)

if submit:
    # Derive formatted strings from date/time pickers
    contractor_birthdate = (
        contractor_birthdate_raw.strftime("%d/%m/%Y") if contractor_birthdate_raw else ""
    )
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
        "Duração (horas)": event_duration_hours,
        "Horário início": event_start_time_str,
        "Horário término": event_end_time_str,
        "Máximo de convidados": guest_count or 0,
        "Pessoas para patinar": skaters_count or 0,
        "1ª atividade": first,
        "2ª atividade": second,
        "3ª atividade": third,
        "Nome da pista": rink_name,
        "Valor total do contrato": contract_total_value or 0.0,
        "Condições de pagamento": payment_terms,
        "Dia de assinatura": signature_day,
        "Mês de assinatura": signature_month,
    })

    if errors:
        st.error("Por favor, corrija os seguintes campos antes de continuar:")
        for e in errors:
            st.markdown(f"- {e}")
    else:
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

        st.divider()
        safe_name = contractor_name.strip().replace(" ", "_")
        safe_date = event_date.replace("/", "-")
        filename = f"contrato_{safe_name}_{safe_date}.docx"
        render_and_download(BIG_TEMPLATE, context, filename)
```

# ─────────────────────────────────────────────

# POCKET EVENT CONTRACT

# ─────────────────────────────────────────────

elif st.session_state.contract_type == “pocket”:

```
st.header("🎂 Contrato Pocket Event")

with st.form("pocket_contract"):

    st.subheader("👤 Dados do Contratante")

    col1, col2 = st.columns(2)

    with col1:
        contractor_name = st.text_input(
            "Nome do contratante *",
            placeholder="Ex: João Silva",
        )
    with col2:
        contractor_cpf = st.text_input(
            "CPF *",
            placeholder="Ex: 123.456.789-00",
        )

    st.subheader("🎉 Aniversário")

    col3, col4 = st.columns(2)

    with col3:
        birthday_person = st.text_input(
            "Nome do aniversariante *",
            placeholder="Ex: Maria",
        )
    with col4:
        birthday_age = st.number_input(
            "Idade *",
            min_value=0,
            value=None,
            step=1,
            placeholder="Ex: 7",
        )

    st.subheader("📅 Evento")

    col5, col6, col7 = st.columns(3)

    with col5:
        event_date_raw = st.date_input(
            "Data do evento *",
            value=None,
            min_value=date.today(),
            format="DD/MM/YYYY",
        )
    with col6:
        start_time = st.time_input("Horário início *", value=None, step=1800)
    with col7:
        end_time = st.time_input("Horário término *", value=None, step=1800)

    st.subheader("💰 Pagamento")

    col8, col9, col10 = st.columns(3)

    with col8:
        contract_value = st.number_input(
            "Valor do contrato (R$) *",
            min_value=0.0,
            value=None,
            step=50.0,
            format="%.2f",
            placeholder="Ex: 800.00",
        )
    with col9:
        payment_method = st.selectbox(
            "Forma de pagamento *",
            ["PIX", "Cartão de crédito", "Cartão de débito", "Boleto", "Dinheiro", "Outro"],
        )
    with col10:
        payment_date_raw = st.date_input(
            "Data de pagamento *",
            value=None,
            min_value=date.today(),
            format="DD/MM/YYYY",
        )

    st.caption("* Campos obrigatórios")
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
        "Horário início": start_time_str,
        "Horário término": end_time_str,
        "Valor do contrato": contract_value or 0.0,
        "Data de pagamento": payment_date,
    })

    if errors:
        st.error("Por favor, corrija os seguintes campos antes de continuar:")
        for e in errors:
            st.markdown(f"- {e}")
    else:
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

        st.divider()
        safe_name = contractor_name.strip().replace(" ", "_")
        safe_date = event_date.replace("/", "-")
        filename = f"contrato_{safe_name}_{safe_date}.docx"
        render_and_download(POCKET_TEMPLATE, context, filename)
