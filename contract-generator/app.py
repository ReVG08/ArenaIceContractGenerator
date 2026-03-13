import streamlit as st
from docxtpl import DocxTemplate
import tempfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

big_template = os.path.join(BASE_DIR, "contract_template.docx")
pocket_template = os.path.join(BASE_DIR, "pocket_template.docx")

st.set_page_config(page_title="Gerador de Contrato", page_icon="📄")

st.title("Gerador de Contratos - Arena Ice")

contract_type = st.radio(
    "Escolha o tipo de contrato",
    ["Evento Formal", "Pocket Event"]
)

# =========================
# BIG EVENT CONTRACT
# =========================

if contract_type == "Evento Grande":

    with st.form("big_contract"):

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

        first = st.text_input("Horário primeira atividade")
        second = st.text_input("Horário segunda atividade")
        third = st.text_input("Horário terceira atividade")

        rink_name = st.text_input("Nome da pista")

        tipo_espaco = st.selectbox(
            "Tipo de espaço",
            ["Espaço exclusivo", "Arena compartilhada"]
        )

        st.header("Valores")

        contract_total_value = st.number_input("Valor total do contrato (R$)")

        payment_terms = st.text_area("Condições de pagamento")

        signature_day = st.text_input("Dia da assinatura")
        signature_month = st.text_input("Mês da assinatura")

        submit = st.form_submit_button("Gerar contrato")

    if submit:

        doc = DocxTemplate(big_template)

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

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        doc.save(tmp.name)

        with open(tmp.name, "rb") as f:

            st.download_button(
                "Baixar contrato",
                f,
                file_name="contrato_evento.docx"
            )

# =========================
# POCKET EVENT CONTRACT
# =========================

else:

    with st.form("pocket_contract"):

        contractor_name = st.text_input("Nome do contratante")
        contractor_cpf = st.text_input("CPF")

        birthday_person = st.text_input("Nome do aniversariante")
        birthday_age = st.number_input("Idade", step=1)

        event_date = st.text_input("Data do evento")

        start_time = st.text_input("Horário de início")
        end_time = st.text_input("Horário de término")

        contract_value = st.number_input("Valor do contrato (R$)")

        payment_method = st.text_input("Forma de pagamento")
        payment_date = st.text_input("Data do pagamento")

        submit = st.form_submit_button("Gerar contrato")

    if submit:

        doc = DocxTemplate(pocket_template)

        context = {
            "contractor_name": contractor_name,
            "contractor_cpf": contractor_cpf,
            "birthday_person": birthday_person,
            "birthday_age": birthday_age,
            "event_date": event_date,
            "start_time": start_time,
            "end_time": end_time,
            "contract_value": contract_value,
            "payment_method": payment_method,
            "payment_date": payment_date
        }

        doc.render(context)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        doc.save(tmp.name)

        with open(tmp.name, "rb") as f:

            st.download_button(
                "Baixar contrato",
                f,
                file_name="contrato_pocket_event.docx"
            )