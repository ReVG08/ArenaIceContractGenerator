import streamlit as st
from docxtpl import DocxTemplate
import tempfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

big_template = os.path.join(BASE_DIR, "contract_template.docx")
pocket_template = os.path.join(BASE_DIR, "pocket_template.docx")

st.set_page_config(
    page_title="Arena Ice Contract Generator",
    page_icon="⛸️",
    layout="wide"
)

st.title("⛸️ Arena Ice Contract Generator")
st.markdown("Selecione o tipo de contrato abaixo para começar.")

# =====================================================
# CONTRACT SELECTION CARDS
# =====================================================

col1, col2 = st.columns(2)

if "contract_type" not in st.session_state:
    st.session_state.contract_type = None

with col1:
    st.markdown("### 🎉 Evento Grande")
    st.markdown(
        "Eventos completos, aniversários grandes e reservas exclusivas da pista."
    )
    if st.button("Selecionar Evento Grande"):
        st.session_state.contract_type = "big"

with col2:
    st.markdown("### 🎂 Pocket Event")
    st.markdown(
        "Eventos menores e aniversários rápidos com menos variáveis."
    )
    if st.button("Selecionar Pocket Event"):
        st.session_state.contract_type = "pocket"

contract_type = st.session_state.contract_type

# =====================================================
# BIG EVENT CONTRACT
# =====================================================

if contract_type == "big":

    st.divider()
    st.header("🎉 Contrato de Evento Grande")

    with st.form("big_contract"):

        st.subheader("👤 Dados do Contratante")

        col1, col2, col3 = st.columns(3)

        with col1:
            contractor_name = st.text_input(
                "Nome do contratante",
                placeholder="Ex: João Silva"
            )

        with col2:
            contractor_cpf = st.text_input(
                "CPF",
                placeholder="Ex: 123.456.789-00"
            )

        with col3:
            contractor_birthdate = st.text_input(
                "Data de nascimento",
                placeholder="Ex: 12/05/1990"
            )

        st.subheader("📅 Informações do Evento")

        col4, col5, col6 = st.columns(3)

        with col4:
            event_name = st.text_input(
                "Nome do evento",
                value="ANIVERSÁRIO",
                placeholder="Ex: Aniversário da Maria"
            )

        with col5:
            event_date = st.text_input(
                "Data do evento",
                placeholder="Ex: 15/08/2026"
            )

        with col6:
            event_weekday = st.text_input(
                "Dia da semana",
                placeholder="Ex: Sábado"
            )

        col7, col8, col9 = st.columns(3)

        with col7:
            event_duration_hours = st.text_input(
                "Duração (horas)",
                placeholder="Ex: 3"
            )

        with col8:
            event_start_time = st.text_input(
                "Horário início",
                placeholder="Ex: 14:00"
            )

        with col9:
            event_end_time = st.text_input(
                "Horário término",
                placeholder="Ex: 17:00"
            )

        st.subheader("👥 Capacidade")

        col10, col11 = st.columns(2)

        with col10:
            guest_count = st.number_input(
                "Máximo de convidados",
                step=1
            )

        with col11:
            skaters_count = st.number_input(
                "Pessoas para patinar",
                step=1
            )

        st.subheader("🎯 Programação")

        col12, col13, col14 = st.columns(3)

        with col12:
            first = st.text_input(
                "1ª atividade",
                placeholder="Ex: 14:30 - Entrada na pista"
            )

        with col13:
            second = st.text_input(
                "2ª atividade",
                placeholder="Ex: 15:30 - Corte do bolo"
            )

        with col14:
            third = st.text_input(
                "3ª atividade",
                placeholder="Ex: 16:30 - Encerramento"
            )

        st.subheader("🏟️ Arena")

        rink_name = st.text_input(
            "Nome da pista",
            placeholder="Ex: Arena Ice Brasil"
        )

        tipo_espaco = st.selectbox(
            "Tipo de espaço",
            ["Espaço exclusivo", "Arena compartilhada"]
        )

        st.subheader("💰 Valores")

        contract_total_value = st.number_input(
            "Valor total do contrato (R$)"
        )

        payment_terms = st.text_area(
            "Condições de pagamento",
            placeholder="Ex: 50% via PIX na assinatura e 50% até 3 dias antes do evento."
        )

        st.subheader("✍️ Assinatura")

        col15, col16 = st.columns(2)

        with col15:
            signature_day = st.text_input(
                "Dia",
                placeholder="Ex: 12"
            )

        with col16:
            signature_month = st.text_input(
                "Mês",
                placeholder="Ex: Maio"
            )

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
                "📄 Baixar contrato",
                f,
                file_name="contrato_evento_grande.docx"
            )

# =====================================================
# POCKET EVENT CONTRACT
# =====================================================

elif contract_type == "pocket":

    st.divider()
    st.header("🎂 Contrato Pocket Event")

    with st.form("pocket_contract"):

        st.subheader("👤 Dados do Contratante")

        contractor_name = st.text_input(
            "Nome do contratante",
            placeholder="Ex: João Silva"
        )

        contractor_cpf = st.text_input(
            "CPF",
            placeholder="Ex: 123.456.789-00"
        )

        st.subheader("🎉 Aniversário")

        birthday_person = st.text_input(
            "Nome do aniversariante",
            placeholder="Ex: Maria"
        )

        birthday_age = st.number_input(
            "Idade",
            step=1
        )

        st.subheader("📅 Evento")

        event_date = st.text_input(
            "Data do evento",
            placeholder="Ex: 20/09/2026"
        )

        col1, col2 = st.columns(2)

        with col1:
            start_time = st.text_input(
                "Horário início",
                placeholder="Ex: 15:00"
            )

        with col2:
            end_time = st.text_input(
                "Horário término",
                placeholder="Ex: 17:00"
            )

        st.subheader("💰 Pagamento")

        contract_value = st.number_input(
            "Valor do contrato (R$)"
        )

        payment_method = st.text_input(
            "Forma de pagamento",
            placeholder="Ex: PIX"
        )

        payment_date = st.text_input(
            "Data de pagamento",
            placeholder="Ex: 10/09/2026"
        )

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
                "📄 Baixar contrato",
                f,
                file_name="contrato_pocket_event.docx"
            )