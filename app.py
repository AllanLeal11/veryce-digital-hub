import streamlit as st
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

load_dotenv()

st.set_page_config(page_title="Vértice AI Hub", page_icon="🚀", layout="wide")
st.title("🚀 Vértice AI Hub")
st.subheader("Equipo de 9 agentes IA - Soluciones IT para negocios locales")

# Configuración Groq (gratis)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=os.getenv("GROQ_API_KEY")
)

# Sidebar
with st.sidebar:
    st.success("✅ Conectado a Groq (gratis)")
    st.info("📍 Quepos / Puntarenas - Costa Rica")

# Historial
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ejemplo: 'Nuevo lead de un restaurante en Quepos que quiere WhatsApp automatizado'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("El equipo completo está trabajando..."):
            # Prompt del Coordinador (llama a los agentes internos)
            template = """
            Eres el Coordinador General de Vértice Digital.
            Tienes un equipo de 9 agentes especializados.
            Usuario dice: {prompt}

            Responde como equipo completo en español tico, claro y profesional.
            Usa los agentes según necesites: Ventas, Analista, Desarrollador, etc.
            """
            prompt_template = PromptTemplate.from_template(template)
            chain = LLMChain(llm=llm, prompt=prompt_template)
            result = chain.run(prompt=prompt)
            
            st.markdown(result)
    
    st.session_state.messages.append({"role": "assistant", "content": result})
