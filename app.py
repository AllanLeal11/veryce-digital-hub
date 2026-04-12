import streamlit as st
import os
import requests
import base64
import json
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
NETLIFY_TOKEN   = os.getenv("NETLIFY_TOKEN")
NETLIFY_SITE_ID = os.getenv("NETLIFY_SITE_ID")  # opcional, si ya tiene sitio

# ─── AGENTES: DEFINICIÓN ──────────────────────────────────────────────────────
AGENTES = {
    "ventas": {
        "nombre": "💼 Carlos — Ventas",
        "keywords": ["propuesta", "precio", "cotiz", "vender", "cliente", "lead", "paquete", "costo"],
        "prompt": """Eres Carlos, agente de Ventas de Vértice Digital. Tu jefe directo es Allan Leal, CEO.
Cuando él pide una propuesta o cotización, la entregas INMEDIATAMENTE en formato estructurado con precios en colones costarricenses.
Contexto: empresa IT en Liberia, Guanacaste, Costa Rica. Servicios: webs, WhatsApp Business, facturación electrónica, POS, automatizaciones.
Precios de referencia: Web básica ₡150,000-₡300,000 | Web completa ₡300,000-₡600,000 | WhatsApp Bot ₡200,000 | Facturación electrónica ₡150,000 | POS ₡400,000
NUNCA pidas reuniones. NUNCA preguntes si quieres más info. ENTREGA el contenido solicitado."""
    },
    "desarrollador": {
        "nombre": "💻 Rodrigo — Desarrollador",
        "keywords": ["código", "codigo", "web", "html", "css", "javascript", "página", "pagina", "sitio", "deploy", "netlify", "desarrolla", "crea la web", "haz la web"],
        "prompt": """Eres Rodrigo, Desarrollador Senior de Vértice Digital. Tu jefe es Allan Leal, CEO.
Cuando Allan pide código, lo entregas COMPLETO e inmediatamente. No pides confirmaciones ni permisos.
Especializaciones: HTML/CSS/JS, sitios para negocios ticos, integración WhatsApp, formularios de contacto.
Si piden una web, entrega el HTML completo, funcional, con diseño profesional en español tico.
USA siempre colores modernos, diseño responsivo, y menciona Liberia/Guanacaste/Costa Rica si aplica.
NUNCA digas "primero necesito saber..." — ENTREGA el código solicitado de una vez."""
    },
    "diseñador": {
        "nombre": "🎨 Sofía — Diseñadora UI/UX",
        "keywords": ["diseño", "diseña", "color", "logo", "estilo", "branding", "paleta", "tipografía", "ux", "ui", "wireframe"],
        "prompt": """Eres Sofía, Diseñadora UI/UX de Vértice Digital. Tu jefe es Allan Leal, CEO.
Entregas propuestas de diseño concretas: paletas de colores con códigos hex, tipografías, estructura de páginas.
Contexto: negocios locales en Guanacaste, Costa Rica. Estilos modernos, tropicales, profesionales.
Cuando piden diseño, entregas especificaciones exactas y listos para implementar. Sin rodeos."""
    },
    "pm": {
        "nombre": "📋 Mariana — Project Manager",
        "keywords": ["proyecto", "plan", "cronograma", "plazo", "etapa", "fase", "timeline", "avance", "tareas"],
        "prompt": """Eres Mariana, Project Manager de Vértice Digital. Tu jefe es Allan Leal, CEO.
Cuando Allan pide un plan de proyecto, lo entregas en formato tabla con etapas, días y responsables.
Usas metodología ágil adaptada a equipos pequeños. Los proyectos son para negocios en Costa Rica.
ENTREGA el cronograma inmediatamente, sin hacer preguntas previas."""
    },
    "marketing": {
        "nombre": "📣 Diego — Marketing Local",
        "keywords": ["marketing", "redes", "instagram", "facebook", "post", "contenido", "campaña", "anuncio", "publicidad", "seo"],
        "prompt": """Eres Diego, especialista en Marketing Local de Vértice Digital. Tu jefe es Allan Leal, CEO.
Te especializas en marketing digital para negocios en Guanacaste y Costa Rica.
Entregas estrategias concretas, textos para posts, ideas de contenido, copys publicitarios.
Cuando piden contenido, lo redactas completo y listo para publicar. En español tico natural."""
    },
    "soporte": {
        "nombre": "🔧 Kevin — Soporte Técnico",
        "keywords": ["error", "falla", "bug", "problema", "no funciona", "soporte", "ayuda técnica", "configurar", "instalar"],
        "prompt": """Eres Kevin, Soporte Técnico de Vértice Digital. Tu jefe es Allan Leal, CEO.
Cuando Allan reporta un problema técnico, diagnosticas y das solución paso a paso inmediatamente.
Especializaciones: Railway, Netlify, WhatsApp Business API, Hacienda CR (facturación electrónica), POS.
NUNCA pidas tickets ni procedimientos burocráticos. Solución directa y clara."""
    },
    "automatizacion": {
        "nombre": "⚙️ Luis — Automatización",
        "keywords": ["automatiza", "automatización", "n8n", "bot", "workflow", "integración", "whatsapp", "api", "zapier", "make"],
        "prompt": """Eres Luis, Experto en Automatización de Vértice Digital. Tu jefe es Allan Leal, CEO.
Diseñas flujos de automatización con n8n, WhatsApp Business, APIs de facturación electrónica de Costa Rica.
Cuando piden un flujo, lo describes paso a paso con nodos específicos de n8n o el código necesario.
Contexto: negocios ticos que necesitan automatizar reservas, facturas, respuestas de WhatsApp."""
    },
    "admin": {
        "nombre": "📊 Valeria — Administración/Finanzas",
        "keywords": ["factura", "contrato", "pago", "finanzas", "admin", "reporte financiero", "cobro", "presupuesto"],
        "prompt": """Eres Valeria, Administrativa/Finanzas de Vértice Digital. Tu jefa es Allan Leal, CEO.
Manejas contratos, facturas, reportes financieros y presupuestos.
Cuando Allan pide un documento administrativo, lo redactas completo con formato profesional.
Precios en colones costarricenses. Incluye SINPE Móvil como método de pago estándar."""
    },
    "analista": {
        "nombre": "🔍 Andrea — Analista de Requerimientos",
        "keywords": ["requisitos", "requerimientos", "necesita", "qué quiere", "especificación", "análisis"],
        "prompt": """Eres Andrea, Analista de Requerimientos de Vértice Digital. Tu jefe es Allan Leal, CEO.
Cuando Allan te pide analizar qué necesita un cliente, entregas una ficha estructurada de requerimientos.
Incluye: funcionalidades necesarias, tecnologías recomendadas, estimación de horas, complejidad.
Para negocios en Costa Rica: restaurants, hoteles, pulperías, ferreterías, clínicas, abogados."""
    },
    "coordinador": {
        "nombre": "🤖 Sistema — Coordinador",
        "keywords": [],
        "prompt": """Eres el sistema de coordinación de Vértice Digital. El jefe es Allan Leal, CEO.
Tu rol es responder solicitudes generales y coordinar. SIEMPRE reconoces a Allan como jefe y CEO.
Cuando no es claro qué agente debe responder, tú respondes de forma directa y útil.
NUNCA pidas reuniones. NUNCA preguntes si quieres más información antes de responder.
Contexto: empresa IT en Liberia, Guanacaste, Costa Rica. Servicios a negocios locales."""
    }
}

# ─── FUNCIONES UTILITARIAS ────────────────────────────────────────────────────

def detectar_agente(mensaje: str) -> str:
    """Detecta qué agente debe responder según keywords."""
    msg = mensaje.lower()
    for agente_id, agente in AGENTES.items():
        if agente_id == "coordinador":
            continue
        for kw in agente["keywords"]:
            if kw in msg:
                return agente_id
    return "coordinador"


def llamar_groq(sistema: str, historial: list, mensaje: str) -> str:
    """Llama a Groq con el historial completo."""
    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.6,
            api_key=GROQ_API_KEY
        )
        messages = [("system", sistema)]
        for h in historial[-10:]:  # últimos 10 turnos para contexto
            messages.append((h["role"], h["content"]))
        messages.append(("human", mensaje))
        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | llm
        return chain.invoke({}).content
    except Exception as e:
        return f"❌ Error al conectar con Groq: {e}"


def generar_pdf(contenido: str, titulo: str) -> bytes:
    """Genera un PDF simple con el contenido dado."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib import colors
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()

        # Estilo personalizado
        estilo_titulo = ParagraphStyle(
            'Titulo', parent=styles['Title'],
            fontSize=18, textColor=colors.HexColor('#1a1a2e'), spaceAfter=20
        )
        estilo_subtitulo = ParagraphStyle(
            'Sub', parent=styles['Heading2'],
            fontSize=12, textColor=colors.HexColor('#16213e'), spaceAfter=10
        )
        estilo_normal = ParagraphStyle(
            'Normal2', parent=styles['Normal'],
            fontSize=10, leading=16, spaceAfter=8
        )

        story = []
        story.append(Paragraph("🚀 Vértice Digital", estilo_titulo))
        story.append(Paragraph("Soluciones IT para negocios en Liberia, Guanacaste, Costa Rica", estilo_normal))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(titulo, estilo_subtitulo))
        story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_normal))
        story.append(Spacer(1, 0.2 * inch))

        # Procesar líneas del contenido
        for linea in contenido.split('\n'):
            linea = linea.strip()
            if not linea:
                story.append(Spacer(1, 0.1 * inch))
            elif linea.startswith('#'):
                texto = linea.lstrip('#').strip()
                story.append(Paragraph(texto, estilo_subtitulo))
            else:
                linea_safe = linea.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(linea_safe, estilo_normal))

        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Vértice Digital | Liberia, Guanacaste, Costa Rica", estilo_normal))
        story.append(Paragraph("Tel: +506 XXXX-XXXX | vertice.digital", estilo_normal))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    except Exception as e:
        return None


def deploy_netlify(html_code: str, nombre_sitio: str = None) -> dict:
    """Despliega HTML a Netlify y retorna la URL."""
    if not NETLIFY_TOKEN:
        return {"ok": False, "error": "Falta NETLIFY_TOKEN en las variables de Railway"}

    headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type": "application/zip"
    }

    try:
        import io, zipfile

        # Crear ZIP con index.html
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.html", html_code)
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()

        if NETLIFY_SITE_ID:
            # Deploy a sitio existente
            url = f"https://api.netlify.com/api/v1/sites/{NETLIFY_SITE_ID}/deploys"
        else:
            # Crear sitio nuevo
            url = "https://api.netlify.com/api/v1/sites"

        response = requests.post(url, headers=headers, data=zip_bytes, timeout=30)

        if response.status_code in [200, 201]:
            data = response.json()
            site_url = data.get("ssl_url") or data.get("url") or data.get("deploy_ssl_url", "")
            return {"ok": True, "url": site_url, "id": data.get("id", "")}
        else:
            return {"ok": False, "error": f"Error Netlify {response.status_code}: {response.text[:200]}"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def extraer_html(texto: str) -> str | None:
    """Extrae bloque HTML de la respuesta del agente."""
    import re
    # Busca bloques ```html ... ```
    match = re.search(r'```html\s*(.*?)```', texto, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Busca <!DOCTYPE o <html directo
    match = re.search(r'(<!DOCTYPE html.*?</html>)', texto, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


# ─── UI STREAMLIT ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Vértice AI Hub — Panel del CEO",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    .agente-badge {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        color: #e2e8f0;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 6px;
    }
    .ceo-badge {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/1a1a2e/e2e8f0?text=Vértice+Digital", use_column_width=True)
    st.markdown("---")
    st.markdown("### 👑 Panel CEO")
    st.markdown("**Allan Leal** — CEO & Fundador")
    st.markdown("📍 Liberia, Guanacaste, Costa Rica")
    st.markdown("---")
    st.markdown("### 👥 Tu Equipo")
    for aid, ag in AGENTES.items():
        if aid != "coordinador":
            st.markdown(f"• {ag['nombre']}")
    st.markdown("---")

    # Config Netlify
    with st.expander("⚙️ Config Netlify"):
        netlify_ok = "✅" if NETLIFY_TOKEN else "❌ Falta NETLIFY_TOKEN"
        st.markdown(f"Token: {netlify_ok}")
        if not NETLIFY_TOKEN:
            st.info("Agrega NETLIFY_TOKEN en Railway → Variables")

    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ─── MAIN ─────────────────────────────────────────────────────────────────────
st.markdown("# 🚀 Vértice AI Hub")
st.markdown("**Panel de Control CEO** — Da órdenes directas a tu equipo de agentes IA")

if not GROQ_API_KEY:
    st.error("⚠️ Falta GROQ_API_KEY en Railway → Settings → Variables")
    st.stop()

# Estado de sesión
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Buenos días, Allan. Tu equipo está listo. ¿Cuál es la primera orden del día?",
        "agente": "🤖 Sistema"
    })

# Mostrar historial
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f'<span class="ceo-badge">👑 Allan — CEO</span>', unsafe_allow_html=True)
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            agente_label = msg.get("agente", "🤖 Agente")
            st.markdown(f'<span class="agente-badge">{agente_label}</span>', unsafe_allow_html=True)
            st.markdown(msg["content"])

            # Botones de acción si hay PDF o HTML guardado
            if msg.get("pdf_content"):
                pdf_bytes = generar_pdf(msg["pdf_content"], msg.get("pdf_titulo", "Documento"))
                if pdf_bytes:
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"vertice_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{msg.get('ts', id(msg))}"
                    )

            if msg.get("html_content"):
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Descargar HTML",
                        data=msg["html_content"],
                        file_name="index.html",
                        mime="text/html",
                        key=f"html_{msg.get('ts', id(msg))}"
                    )
                with col2:
                    if st.button("🚀 Deploy a Netlify", key=f"deploy_{msg.get('ts', id(msg))}"):
                        with st.spinner("Desplegando en Netlify..."):
                            resultado = deploy_netlify(msg["html_content"])
                        if resultado["ok"]:
                            st.success(f"✅ Sitio publicado: [{resultado['url']}]({resultado['url']})")
                        else:
                            st.error(f"❌ {resultado['error']}")

# ─── INPUT DEL CEO ────────────────────────────────────────────────────────────
if orden := st.chat_input("Escribe tu orden aquí, Allan..."):

    # Mostrar mensaje del CEO
    st.session_state.messages.append({"role": "user", "content": orden})
    with st.chat_message("user"):
        st.markdown(f'<span class="ceo-badge">👑 Allan — CEO</span>', unsafe_allow_html=True)
        st.markdown(orden)

    # Detectar agente
    agente_id = detectar_agente(orden)
    agente_info = AGENTES[agente_id]

    # Construir historial para el LLM (solo texto)
    historial_llm = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    # Llamar al agente
    with st.chat_message("assistant"):
        with st.spinner(f"{agente_info['nombre']} está trabajando..."):
            respuesta = llamar_groq(agente_info["prompt"], historial_llm, orden)

        st.markdown(f'<span class="agente-badge">{agente_info["nombre"]}</span>', unsafe_allow_html=True)
        st.markdown(respuesta)

        # Guardar en sesión
        msg_data = {
            "role": "assistant",
            "content": respuesta,
            "agente": agente_info["nombre"],
            "ts": datetime.now().strftime("%H%M%S")
        }

        # ¿Hay HTML en la respuesta?
        html_detectado = extraer_html(respuesta)
        if html_detectado:
            msg_data["html_content"] = html_detectado
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Descargar HTML",
                    data=html_detectado,
                    file_name="index.html",
                    mime="text/html",
                    key=f"html_new_{datetime.now().strftime('%H%M%S%f')}"
                )
            with col2:
                if st.button("🚀 Deploy a Netlify", key=f"deploy_new_{datetime.now().strftime('%H%M%S%f')}"):
                    with st.spinner("Desplegando en Netlify..."):
                        resultado = deploy_netlify(html_detectado)
                    if resultado["ok"]:
                        st.success(f"✅ Sitio en línea: [{resultado['url']}]({resultado['url']})")
                    else:
                        st.error(f"❌ {resultado['error']}")

        # Botón PDF para propuestas/documentos
        palabras_pdf = ["propuesta", "cotiz", "presupuesto", "contrato", "plan", "reporte", "oferta"]
        if any(p in orden.lower() for p in palabras_pdf):
            msg_data["pdf_content"] = respuesta
            msg_data["pdf_titulo"] = f"Propuesta Vértice Digital — {datetime.now().strftime('%d/%m/%Y')}"
            pdf_bytes = generar_pdf(respuesta, msg_data["pdf_titulo"])
            if pdf_bytes:
                st.download_button(
                    label="📄 Descargar Propuesta en PDF",
                    data=pdf_bytes,
                    file_name=f"propuesta_vertice_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key=f"pdf_new_{datetime.now().strftime('%H%M%S%f')}"
                )

        st.session_state.messages.append(msg_data)
