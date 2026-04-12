import streamlit as st
from crew import create_crew
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Vértice AI Hub", page_icon="🚀", layout="wide")
st.title("🚀 Vértice AI Hub")
st.subheader("Tu equipo de 9 agentes IA para soluciones IT locales")

# Sidebar
with st.sidebar:
    st.header("Equipo Vértice")
    st.write("✅ 9 agentes activos")
    st.write("📍 Quepos / Puntarenas - Costa Rica")
    api_key = st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

# Chat principal
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Escribe aquí lo que necesitas (ej: nuevo lead de restaurante)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("El equipo completo está trabajando..."):
            crew = create_crew(prompt)
            result = crew.kickoff()
            st.markdown(result)
    
    st.session_state.messages.append({"role": "assistant", "content": result})