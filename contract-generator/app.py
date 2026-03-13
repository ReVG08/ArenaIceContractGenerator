import streamlit as st
from docxtpl import DocxTemplate
import tempfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(BASE_DIR, "contract_template.docx")

st.set_page_config(
    page_title="Gerador de Contrato",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Gerador de Contrato de Evento")
st.caption("Preencha as informações abaixo para gerar automaticamente o contrato.")

with st.form("formulario_contrato"):

    st.divider()
    st.subheader("👤 Dados do Contratante")

    col1, col2, col3 = st.columns(3)

    with col1:
        contractor_name = st.text_input(
            "Nome do contratante",
            placeholder="Ex: João da Silva"
        )

    with col2:
        contractor_cpf = st.text_input(
            "CPF",
            placeholder="000.000.000-00"
        )

    with col3:
        contractor_birthdate = st.text_input(
            "Data de nascimento",
            placeholder="DD/MM/AAAA"
        )

    st.divider()
    st.subheader("🎉 Informações do Evento")

    col1, col2, col3 = st.columns(3)

    with col1:
        event_name = st.text_input(
            "Nome do evento",
            value="ANIVERSÁRIO"
        )

    with col2:
        event_date = st.text_input(
            "Data do evento",
            placeholder="DD/MM/AAAA"
        )

    with col3:
        event_weekday = st.text_input(
            "Dia da semana",
            placeholder="Ex: Sábado"
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        event_duration_hours = st.text_input(
            "Duração do evento (horas)",
            placeholder="Ex: 3"
        )

    with col2:
        event_start_time = st.text_input(
            "Horário de início",
            placeholder="Ex: 14:00"
        )

    with col3:
        event_end_time = st.text_input(
            "Horário de término",
            placeholder="Ex: 17:00"
        )

    st.divider()
    st.subheader("⛸️ Participantes e Atividades")

    col1, col2 = st.columns(2)

    with col1:
        guest_count = st.number_input(
            "Número máximo de convidados",
            step=1
        )

        skaters_count = st.number_input(
            "Número de pessoas para patinar",
            step=1
        )

        rink_name = st.text_input(
            "Nome da pista",
            placeholder="Ex: Pista Central"
        )

    with col2:
        tipo_espaco = st.selectbox(
            "Tipo de espaço",
            ["Espaço exclusivo", "Arena compartilhada"]
        )

        first = st.text_input(
            "Horário primeira atividade",
            placeholder="Ex: 14:30"
        )

        second = st.text_input(
            "Horário segunda atividade",
            placeholder="Ex: 15:30"
        )

        third = st.text_input(
            "Horário terceira atividade",
            placeholder="Ex: 16:30"
        )

    st.divider()
    st.subheader("💰 Valores")

    contract_total_value = st.number_input(
        "Valor total do contrato (R$)",
        step=100
    )

    st.divider()
    st.subheader("💳 Condições de Pagamento")

    payment_terms = st.text_area(
        "Descreva as condições de pagamento",
        height=150,
        placeholder="Ex: 50% na assinatura e 50% até o dia do evento."
    )

    st.divider()
    st.subheader("✍️ Assinatura")

    col1, col2 = st.columns(2)

    with col1:
        signature_day = st.text_input(
            "Dia da assinatura",
            placeholder="Ex: 15"
        )

    with col2:
        signature_month = st.text_input(
            "Mês da assinatura",
            placeholder="Ex: Março"
        )

    st.divider()

    submit = st.form_submit_button("📄 Gerar contrato")

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
        "signature_month": signature_month,
        "first": first,
        "second": second,
        "third": third
    }

    doc.render(context)

    tmp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp_docx.name)

    with open(tmp_docx.name, "rb") as f:

        st.success("✅ Contrato gerado com sucesso!")

        st.download_button(
            "⬇️ Baixar contrato",
            f,
            file_name="contrato_evento.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )