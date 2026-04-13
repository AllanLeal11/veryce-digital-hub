import streamlit as st
import os
import requests
import io
import zipfile
import re
from datetime import datetime
from dotenv import load_dotenv
# langchain eliminado — usamos Groq client directo para evitar errores con {} en CSS/JS

load_dotenv()

GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
NETLIFY_TOKEN   = os.getenv("NETLIFY_TOKEN")
NETLIFY_SITE_ID = os.getenv("NETLIFY_SITE_ID")

# ─── CONTEXTO BASE COMPARTIDO (no se repite en cada agente) ───────────────────
CTX = "Vértice Digital, IT en Liberia, Guanacaste, CR. Jefe: Allan Leal (CEO). Servicios: webs, WhatsApp Bot, facturación electrónica, POS, automatizaciones. Precios en ₡. NUNCA pidas reuniones ni info previa. ENTREGA inmediatamente."

# ─── AGENTES: prompt mínimo, solo lo diferencial ─────────────────────────────
AGENTES = {
    "ventas": {
        "nombre": "💼 Carlos — Ventas",
        "keywords": ["propuesta", "precio", "cotiz", "vender", "cliente", "lead", "paquete", "costo", "oferta"],
        "prompt": f"{CTX}\nEres Carlos, Ventas. Entrega cotizaciones y propuestas al instante. Ref: Web básica ₡150k-₡300k | Web completa ₡300k-₡600k | WhatsApp Bot ₡200k | Facturación ₡150k | POS ₡400k. Incluye desglose, SINPE Móvil y próximos pasos.",
    },
    "desarrollador": {
        "nombre": "💻 Rodrigo — Desarrollador",
        "keywords": ["código", "codigo", "web", "html", "css", "página", "pagina", "sitio", "desarrolla", "crea la web", "haz la web", "programa"],
        "prompt": f"""{CTX}
Eres Rodrigo, Desarrollador Senior especializado en webs de alto impacto visual.
Al pedir una web, entrega TODO en UN SOLO bloque ```html autónomo.

REGLAS TÉCNICAS OBLIGATORIAS:
- CSS SIEMPRE dentro de <style> en el <head>. NUNCA href a .css externo.
- JS SIEMPRE dentro de <script> al final del <body>. NUNCA src a .js externo.
- Puedes usar CDNs: Bootstrap 5, Font Awesome 6, Google Fonts.

REGLAS DE DISEÑO OBLIGATORIAS (aplica SIEMPRE):
- Fondo oscuro: #0d1b2a o similar. Nunca fondo blanco genérico.
- Navbar fija con efecto blur al hacer scroll.
- Hero con gradiente animado, texto grande impactante y CTA dorado.
- Paleta: azul marino + dorado (#f0a500) + blanco. Variables CSS.
- Tarjetas con hover effect (transform + sombra).
- Animaciones fade-in al hacer scroll con IntersectionObserver.
- Botón flotante de WhatsApp con efecto pulse.
- Sección de servicios con íconos Font Awesome.
- Footer completo con links y redes sociales.
- 100% responsivo mobile-first.
- Fuentes: Google Fonts Syne (títulos) + Space Grotesk (cuerpo).

NUNCA hagas webs planas, sin animaciones o con mucho espacio vacío.
Sin preguntas. Entrega el HTML completo de una vez.""",
    },
    "diseñador": {
        "nombre": "🎨 Sofía — Diseñadora UI/UX",
        "keywords": ["diseño", "diseña", "color", "logo", "estilo", "branding", "paleta", "tipografía", "ux", "ui"],
        "prompt": f"{CTX}\nEres Sofía, Diseñadora. Entrega paletas hex, tipografías y estructura visual concreta. Estilo moderno tropical profesional.",
    },
    "pm": {
        "nombre": "📋 Mariana — Project Manager",
        "keywords": ["proyecto", "plan", "cronograma", "plazo", "etapa", "fase", "timeline", "avance"],
        "prompt": f"{CTX}\nEres Mariana, PM. Entrega cronogramas en tabla markdown con etapas, días y responsables. Metodología ágil.",
    },
    "marketing": {
        "nombre": "📣 Diego — Marketing Local",
        "keywords": ["marketing", "redes", "instagram", "facebook", "post", "contenido", "campaña", "anuncio", "publicidad", "seo", "copy"],
        "prompt": f"{CTX}\nEres Diego, Marketing. Entrega copies, posts y estrategias listos para publicar en español tico. Enfocado en Guanacaste.",
    },
    "soporte": {
        "nombre": "🔧 Kevin — Soporte Técnico",
        "keywords": ["error", "falla", "bug", "problema", "no funciona", "soporte", "configurar", "instalar"],
        "prompt": f"{CTX}\nEres Kevin, Soporte. Diagnostica y da solución paso a paso al instante. Especialidades: Railway, Netlify, WhatsApp API, Hacienda CR, POS.",
    },
    "automatizacion": {
        "nombre": "⚙️ Luis — Automatización",
        "keywords": ["automatiza", "automatización", "n8n", "bot", "workflow", "integración", "whatsapp", "api", "flujo"],
        "prompt": f"{CTX}\nEres Luis, Automatización. Diseña flujos con n8n, WhatsApp Business, APIs Hacienda CR. Entrega nodos específicos o código listo.",
    },
    "admin": {
        "nombre": "📊 Valeria — Admin/Finanzas",
        "keywords": ["factura", "contrato", "pago", "finanzas", "admin", "reporte", "cobro", "presupuesto"],
        "prompt": f"{CTX}\nEres Valeria, Administración. Redacta contratos, facturas y reportes completos. Precios en ₡, incluye SINPE Móvil.",
    },
    "analista": {
        "nombre": "🔍 Andrea — Analista",
        "keywords": ["requisitos", "requerimientos", "necesita", "análisis", "especificación", "ficha"],
        "prompt": f"{CTX}\nEres Andrea, Analista. Entrega fichas con funcionalidades, tecnologías, horas estimadas y complejidad.",
    },
    "coordinador": {
        "nombre": "🤖 Coordinador",
        "keywords": [],
        "prompt": f"{CTX}\nEres el coordinador. Responde órdenes generales de forma directa. Allan es tu jefe.",
    }
}

# ─── ROUTING ──────────────────────────────────────────────────────────────────
def detectar_agente_keywords(mensaje: str) -> str:
    msg = mensaje.lower()
    for aid, ag in AGENTES.items():
        if aid == "coordinador":
            continue
        if any(kw in msg for kw in ag["keywords"]):
            return aid
    return "coordinador"

def detectar_agente_llm(mensaje: str) -> str:
    """Llama al modelo 8B SOLO si keywords no detectaron nada. Costo mínimo."""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        ids = [k for k in AGENTES if k != "coordinador"]
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"Clasifica en UNA de: {', '.join(ids)}, coordinador. Responde solo la palabra."},
                {"role": "user", "content": mensaje}
            ],
            temperature=0,
            max_tokens=10,
        )
        r = resp.choices[0].message.content.strip().lower()
        return r if r in AGENTES else "coordinador"
    except:
        return "coordinador"

# ─── COMPRESIÓN DE HISTORIAL ──────────────────────────────────────────────────
def comprimir_historial(historial: list) -> list:
    """Mantiene últimos 4 mensajes. El resto se convierte en resumen compacto."""
    if len(historial) <= 4:
        return historial
    viejos = historial[:-4]
    recientes = historial[-4:]
    resumen = "Contexto previo:\n" + "\n".join(
        f"{'Allan' if m['role']=='user' else 'Agente'}: {m['content'][:60]}..."
        for m in viejos
    )
    return [{"role": "user", "content": resumen},
            {"role": "assistant", "content": "Ok."}] + recientes

# ─── LLAMADA PRINCIPAL (70B) ──────────────────────────────────────────────────
def llamar_groq(sistema: str, historial: list, mensaje: str) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        msgs = [{"role": "system", "content": sistema}]
        for h in comprimir_historial(historial):
            msgs.append({"role": h["role"], "content": h["content"]})
        msgs.append({"role": "user", "content": mensaje})
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            temperature=0.6,
            max_tokens=3000,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"

# ─── PDF ──────────────────────────────────────────────────────────────────────
def generar_pdf(contenido: str, titulo: str) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        sT = ParagraphStyle('T', parent=styles['Title'], fontSize=18,
                            textColor=colors.HexColor('#1a1a2e'), spaceAfter=14)
        sS = ParagraphStyle('S', parent=styles['Heading2'], fontSize=12,
                            textColor=colors.HexColor('#16213e'), spaceAfter=8)
        sN = ParagraphStyle('N', parent=styles['Normal'], fontSize=10,
                            leading=16, spaceAfter=6)

        story = [
            Paragraph("Vértice Digital", sT),
            Paragraph("Liberia, Guanacaste, Costa Rica", sN),
            Spacer(1, 0.1*inch),
            Paragraph(titulo, sS),
            Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", sN),
            Spacer(1, 0.15*inch),
        ]
        for linea in contenido.split('\n'):
            linea = linea.strip()
            if not linea:
                story.append(Spacer(1, 0.07*inch))
            elif linea.startswith('#'):
                story.append(Paragraph(linea.lstrip('#').strip(), sS))
            else:
                safe = linea.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                story.append(Paragraph(safe, sN))
        story.append(Paragraph("vertice.digital", sN))
        doc.build(story)
        buf.seek(0)
        return buf.read()
    except:
        return None

# ─── NETLIFY ──────────────────────────────────────────────────────────────────
def deploy_netlify(html: str) -> dict:
    if not NETLIFY_TOKEN:
        return {"ok": False, "error": "Falta NETLIFY_TOKEN en Railway → Variables"}
    try:
        zb = io.BytesIO()
        with zipfile.ZipFile(zb, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.html", html)
        zb.seek(0)
        url = (f"https://api.netlify.com/api/v1/sites/{NETLIFY_SITE_ID}/deploys"
               if NETLIFY_SITE_ID else "https://api.netlify.com/api/v1/sites")
        r = requests.post(url,
                          headers={"Authorization": f"Bearer {NETLIFY_TOKEN}",
                                   "Content-Type": "application/zip"},
                          data=zb.read(), timeout=30)
        if r.status_code in [200, 201]:
            d = r.json()
            return {"ok": True, "url": d.get("ssl_url") or d.get("url", "")}
        return {"ok": False, "error": f"Netlify {r.status_code}: {r.text[:150]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def extraer_html(texto: str) -> str | None:
    m = re.search(r'```html\s*(.*?)```', texto, re.DOTALL | re.IGNORECASE)
    if m: return limpiar_html(m.group(1).strip())
    m = re.search(r'(<!DOCTYPE html.*?</html>)', texto, re.DOTALL | re.IGNORECASE)
    if m: return limpiar_html(m.group(1).strip())
    return None

def limpiar_html(html: str) -> str:
    """
    Detecta y advierte si el HTML tiene referencias a archivos externos locales.
    Los CDNs (http/https) se dejan pasar. Solo bloquea hrefs/srcs relativos.
    """
    import re as _re
    # Detectar links a .css locales
    externos_css = _re.findall(r'<link[^>]+href=["\']((?!https?://)[^"\']+\.css)["\']', html, _re.IGNORECASE)
    externos_js  = _re.findall(r'<script[^>]+src=["\']((?!https?://)[^"\']+\.js)["\']', html, _re.IGNORECASE)
    
    for f in externos_css:
        # Eliminar el <link> externo — el CSS ya debería estar en <style>
        html = _re.sub(rf'<link[^>]+href=["\']{_re.escape(f)}["\'"][^>]*/?>', '', html)
    for f in externos_js:
        # Eliminar el <script src> externo — el JS ya debería estar inline
        html = _re.sub(rf'<script[^>]+src=["\']{_re.escape(f)}["\'"][^>]*></script>', '', html)
    
    return html

# ─── PREVIEW HTML ─────────────────────────────────────────────────────────────

def mostrar_preview_html(html: str, ts: str):
    """Muestra preview inline del HTML + botón de descarga. Sin deploy automático."""
    import base64

    # Botón de descarga
    st.download_button(
        label="📥 Descargar HTML",
        data=html,
        file_name=f"demo_vertice_{ts}.html",
        mime="text/html",
        key=f"dl_{ts}"
    )

    # Preview inline con iframe usando data URI
    html_b64 = base64.b64encode(html.encode()).decode()
    iframe_code = f"""
    <div style="border:1px solid rgba(255,255,255,0.1);border-radius:12px;overflow:hidden;margin-top:0.5rem;">
        <div style="background:#1a1a2e;padding:8px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid rgba(255,255,255,0.08);">
            <span style="width:10px;height:10px;border-radius:50%;background:#ff5f57;display:inline-block"></span>
            <span style="width:10px;height:10px;border-radius:50%;background:#febc2e;display:inline-block"></span>
            <span style="width:10px;height:10px;border-radius:50%;background:#28c840;display:inline-block"></span>
            <span style="color:rgba(255,255,255,0.4);font-size:11px;margin-left:8px;font-family:monospace;">preview — demo del cliente</span>
        </div>
        <iframe
            src="data:text/html;base64,{html_b64}"
            style="width:100%;height:520px;border:none;display:block;background:#fff;"
            sandbox="allow-scripts allow-same-origin">
        </iframe>
    </div>
    """
    st.markdown(iframe_code, unsafe_allow_html=True)
    st.caption("👆 Revisá la demo. Descargá el HTML y enviásela al cliente cuando estés listo.")


# ─── UI ───────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Vértice AI Hub", page_icon="🚀", layout="wide")
st.markdown("""<style>
.agente-badge{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#e2e8f0;
padding:3px 10px;border-radius:20px;font-size:11px;font-weight:bold;display:inline-block;margin-bottom:5px}
.ceo-badge{background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;
padding:3px 10px;border-radius:20px;font-size:11px;font-weight:bold}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🚀 Vértice AI Hub")
    st.markdown("**Allan Leal** — CEO & Fundador")
    st.markdown("📍 Liberia, Guanacaste, CR")
    st.markdown("---")
    for aid, ag in AGENTES.items():
        if aid != "coordinador":
            st.markdown(f"• {ag['nombre']}")
    st.markdown("---")
    st.markdown(f"**Netlify:** {'✅' if NETLIFY_TOKEN else '❌ Falta token'}")
    if "messages" in st.session_state:
        tokens_est = sum(len(m["content"]) for m in st.session_state.messages) // 4
        st.markdown(f"**~Tokens usados:** `{tokens_est:,}`")
    if st.button("🗑️ Limpiar chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.markdown("# 🚀 Vértice AI Hub — Panel CEO")

if not GROQ_API_KEY:
    st.error("⚠️ Falta GROQ_API_KEY en Railway → Variables")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Buenos días, Allan. Tu equipo está listo. ¿Cuál es la primera orden?",
        "agente": "🤖 Coordinador"
    }]

# Historial
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown('<span class="ceo-badge">👑 Allan — CEO</span>', unsafe_allow_html=True)
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(f'<span class="agente-badge">{msg.get("agente","🤖")}</span>', unsafe_allow_html=True)
            st.markdown(msg["content"])
            ts = msg.get("ts", str(id(msg)))
            if msg.get("pdf_content"):
                pdf = generar_pdf(msg["pdf_content"], msg.get("pdf_titulo", "Propuesta"))
                if pdf:
                    st.download_button("📄 PDF", pdf, f"propuesta_{ts}.pdf",
                                       "application/pdf", key=f"pdf_{ts}")
            if msg.get("html_content"):
                mostrar_preview_html(msg["html_content"], ts)

# Input
if orden := st.chat_input("Escribe tu orden, Allan..."):
    st.session_state.messages.append({"role": "user", "content": orden})
    with st.chat_message("user"):
        st.markdown('<span class="ceo-badge">👑 Allan — CEO</span>', unsafe_allow_html=True)
        st.markdown(orden)

    # Routing: keywords primero (0 tokens), LLM 8B solo si no hay match
    agente_id = detectar_agente_keywords(orden)
    if agente_id == "coordinador":
        agente_id = detectar_agente_llm(orden)

    ag = AGENTES[agente_id]
    historial_llm = [{"role": m["role"], "content": m["content"]}
                     for m in st.session_state.messages[:-1]]

    with st.chat_message("assistant"):
        with st.spinner(f"{ag['nombre']} procesando..."):
            respuesta = llamar_groq(ag["prompt"], historial_llm, orden)

        st.markdown(f'<span class="agente-badge">{ag["nombre"]}</span>', unsafe_allow_html=True)
        st.markdown(respuesta)

        ts = datetime.now().strftime("%H%M%S%f")
        msg_data = {"role": "assistant", "content": respuesta,
                    "agente": ag["nombre"], "ts": ts}

        html = extraer_html(respuesta)
        if html:
            msg_data["html_content"] = html
            mostrar_preview_html(html, ts)

        if any(p in orden.lower() for p in ["propuesta","cotiz","presupuesto","contrato","oferta"]):
            msg_data["pdf_content"] = respuesta
            msg_data["pdf_titulo"] = f"Propuesta — {datetime.now().strftime('%d/%m/%Y')}"
            pdf = generar_pdf(respuesta, msg_data["pdf_titulo"])
            if pdf:
                st.download_button("📄 PDF", pdf, f"propuesta_{ts}.pdf",
                                   "application/pdf", key=f"pdf_new_{ts}")

        st.session_state.messages.append(msg_data)
