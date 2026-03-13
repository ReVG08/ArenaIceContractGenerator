import streamlit as st
from docxtpl import DocxTemplate
import tempfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

big_template = os.path.join(BASE_DIR, "contract_template.docx")
pocket_template = os.path.join(BASE_DIR, "pocket_template.docx")

st.set_page_config(page_title="Gerador de Contratos", page_icon="📄")

st.title("📄 Gerador de Contratos - Arena Ice")

st.markdown("Selecione o tipo de contrato para gerar.")

contract_type = st.radio(
    "Tipo de evento",
    ["Evento Grande", "Pocket Event"],
    horizontal=True
)

# =====================================================
# BIG EVENT CONTRACT
# =====================================================

def big_event_form():

    with st.form("big_contract"):

        st.header("Dados do Contratante")

        col1, col2 = st.columns(2)

        with col1:
            contractor_name = st.text_input("Nome do contratante")

        with col2:
            contractor_cpf = st.text_input("CPF")

        contractor_birthdate = st.text_input("Data de nascimento")

        st.header("Informações do Evento")

        event_name = st.text_input("Nome do evento", value="ANIVERSÁRIO")

        col3, col4 = st.columns(2)

        with col3:
            event_date = st.text_input("Data do evento")

        with col4:
            event_weekday = st.text_input("Dia da semana")

        col5, col6, col7 = st.columns(3)

        with col5:
            event_duration_hours = st.text_input("Duração (horas)")

        with col6:
            event_start_time = st.text_input("Horário início")

        with col7:
            event_end_time = st.text_input("Horário término")

        st.header("Capacidade")

        col8, col9 = st.columns(2)

        with col8:
            guest_count = st.number_input("Máximo de convidados", step=1)

        with col9:
            skaters_count = st.number_input("Pessoas para patinar", step=1)

        st.header("Programação")

        col10, col11, col12 = st.columns(3)

        with col10:
            first = st.text_input("1ª atividade")

        with col11:
            second = st.text_input("2ª atividade")

        with col12:
            third = st.text_input("3ª atividade")

        rink_name = st.text_input("Nome da pista")

        tipo_espaco = st.selectbox(
            "Tipo de espaço",
            ["Espaço exclusivo", "Arena compartilhada"]
        )

        st.header("Valores")

        contract_total_value = st.number_input("Valor total (R$)")

        payment_terms = st.text_area("Condições de pagamento")

        st.header("Assinatura")

        col13, col14 = st.columns(2)

        with col13:
            signature_day = st.text_input("Dia")

        with col14:
            signature_month = st.text_input("Mês")

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

            st.success("Contrato gerado!")

            st.download_button(
                "📥 Baixar contrato",
                f,
                file_name="contrato_evento_grande.docx"
            )


# =====================================================
# POCKET EVENT CONTRACT
# =====================================================

def pocket_event_form():

    with st.form("pocket_contract"):

        st.header("Dados do Contratante")

        contractor_name = st.text_input("Nome do contratante")
        contractor_cpf = st.text_input("CPF")

        st.header("Aniversário")

        birthday_person = st.text_input("Nome do aniversariante")
        birthday_age = st.number_input("Idade", step=1)

        st.header("Evento")

        event_date = st.text_input("Data do evento")

        col1, col2 = st.columns(2)

        with col1:
            start_time = st.text_input("Horário início")

        with col2:
            end_time = st.text_input("Horário término")

        st.header("Pagamento")

        contract_value = st.number_input("Valor (R$)")

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

            st.success("Contrato gerado!")

            st.download_button(
                "📥 Baixar contrato",
                f,
                file_name="contrato_pocket_event.docx"
            )


# =====================================================
# SWITCH UI
# =====================================================

if contract_type == "Evento Grande":
    big_event_form()

else:
    pocket_event_form()