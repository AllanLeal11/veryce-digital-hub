import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

load_dotenv()

st.set_page_config(page_title="Vértice AI Hub", page_icon="🚀", layout="wide")

st.title("🚀 Vértice AI Hub")
st.subheader("Tu equipo de 9 agentes IA - Soluciones IT para negocios locales en Quepos y Puntarenas")

# Verificamos la clave de Groq
groq_key = os.getenv("GROQ_API_KEY")

if not groq_key:
    st.error("⚠️ Falta la variable GROQ_API_KEY en Railway")
    st.info("Ve a Settings → Variables y agrega GROQ_API_KEY con tu clave de Groq.")
else:
    st.success("✅ Conectado a Groq (llama-3.3-70b-versatile)")

with st.sidebar:
    st.success("🌍 Vértice Digital - Quepos, Costa Rica")
    st.info("Soluciones IT: Web • WhatsApp • Facturación • POS")

# Historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("¿Qué necesitas? (ej: lead de restaurante que quiere WhatsApp + facturación)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("El equipo de 9 agentes está trabajando..."):
            try:
                llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    api_key=groq_key
                )

                template = """
                Eres el Coordinador General de Vértice Digital.
                Tienes un equipo de 9 agentes especializados:
                - Ventas
                - Analista de Requerimientos
                - Desarrollador
                - Project Manager
                - Soporte Técnico
                - Marketing Local
                - Diseñador UI/UX
                - Administrativo/Finanzas
                - Experto en Automatización

                Usuario dice: {prompt}

                Responde de forma clara, profesional y en español tico.
                Coordina a los agentes según sea necesario y da una respuesta útil.
                """

                prompt_template = PromptTemplate.from_template(template)
                chain = LLMChain(llm=llm, prompt=prompt_template)
                result = chain.run(prompt=prompt)

                st.markdown(result)
            except Exception as e:
                st.error(f"Error al conectar con Groq: {e}")
                st.info("Revisa que tu GROQ_API_KEY esté correcta en Railway.")

    st.session_state.messages.append({"role": "assistant", "content": result})
