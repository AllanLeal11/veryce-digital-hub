import streamlit as st
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

load_dotenv()

st.set_page_config(page_title="Vértice AI Hub", page_icon="🚀", layout="wide")
st.title("🚀 Vértice AI Hub")
st.subheader("Tu equipo de 9 agentes IA - Soluciones IT locales")

# Groq (gratis)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=os.getenv("GROQ_API_KEY")
)

with st.sidebar:
    st.success("✅ Conectado a Groq (100% gratis)")
    st.info("📍 Guanacaste - Costa Rica")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe aquí lo que necesitas (ej: lead de restaurante en Quepos)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("El equipo de 9 agentes está trabajando..."):
            template = """
            Eres el Coordinador General de Vértice Digital (empresa de soluciones IT para negocios locales en Quepos y Puntarenas).
            Tienes un equipo de 9 agentes: Ventas, Analista, Desarrollador, Project Manager, Soporte, Marketing, Diseñador, Administrativo y tú como Coordinador.
            Usuario dice: {prompt}

            Responde de forma clara, profesional y en español tico. Coordina a los agentes según sea necesario.
            """
            prompt_template = PromptTemplate.from_template(template)
            chain = LLMChain(llm=llm, prompt=prompt_template)
            result = chain.run(prompt=prompt)
            st.markdown(result)
    
    st.session_state.messages.append({"role": "assistant", "content": result})
