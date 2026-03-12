import streamlit as st
from docxtpl import DocxTemplate
import tempfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(BASE_DIR, "contract_template.docx")

st.set_page_config(page_title="Gerador de Contrato", page_icon="📄")

st.title("Gerador de Contrato de Evento")

with st.form("formulario_contrato"):

    st.header("Dados do Contratante")

    contractor_name = st.text_input("Nome do contratante")
    contractor_cpf = st.text_input("CPF")
    contractor_birthdate = st.text_input("Data de nascimento")

    st.header("Informações do Evento")

    event_name = st.text_input("Nome do evento", value="ANIVERSÁRIO")
    event_date = st.text_input("Data do evento")
    event_weekday = st.text_input("Dia da semana")

    event_duration_hours = st.text_input("Duração do evento (horas)")
    event_start_time = st.text_input("Horário de início")
    event_end_time = st.text_input("Horário de término")

    guest_count = st.number_input("Número máximo de convidados", step=1)
    skaters_count = st.number_input("Número de pessoas para patinar", step=1)

    rink_name = st.text_input("Nome da pista")

    tipo_espaco = st.selectbox(
        "Tipo de espaço",
        ["Espaço exclusivo", "Arena compartilhada"]
    )

    st.header("Valores")

    contract_total_value = st.number_input("Valor total do contrato (R$)")

    st.header("Condições de Pagamento")

    payment_terms = st.text_area(
        "Descreva as condições de pagamento",
        height=200
    )

    st.header("Assinatura")

    signature_day = st.text_input("Dia da assinatura")
    signature_month = st.text_input("Mês da assinatura")

    submit = st.form_submit_button("Gerar contrato")

if submit:

    doc = DocxTemplate(template_path)

    context = {
        "contractor_name": contractor_name,
        "contractor_cpf": contractor_cpf,
        "contractor_birthdate": contractor_birthdate,
        "event_name": event_name,
        "event_date": event_date,
        "event_weekday": event_weekday,
        "event_duration_hours": event_duration_hours,
        "event_start_time": event_start_time,
        "event_end_time": event_end_time,
        "guest_count": guest_count,
        "skaters_count": skaters_count,
        "rink_name": rink_name,
        "tipo_espaco": tipo_espaco,
        "contract_total_value": contract_total_value,
        "payment_terms": payment_terms,
        "signature_day": signature_day,
        "signature_month": signature_month
    }

    doc.render(context)

    tmp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp_docx.name)

    with open(tmp_docx.name, "rb") as f:

        st.success("Contrato gerado!")

        st.download_button(
            "Baixar contrato",
            f,
            file_name="contrato_evento.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )