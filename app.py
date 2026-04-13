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
        "prompt": f"""{CTX}
Eres Carlos Mora, Ejecutivo de Ventas de Vértice Digital.
Contacto tuyo: WhatsApp +506 8888-8888 | carlos@vertice.digital

Al generar una propuesta SIEMPRE incluye TODAS estas secciones en orden:

1. ENCABEZADO: Saluda por nombre al cliente/negocio, menciona su giro específico.
2. RESUMEN EJECUTIVO: 2-3 líneas de por qué esta solución es ideal para ese negocio concreto.
3. SERVICIOS PROPUESTOS: Lista detallada con descripción de cada servicio incluido.
4. INVERSIÓN: Precios en colones con símbolo ₡ (NO usar $ ni otros). Ref: Web básica ₡150,000-₡300,000 | Web completa ₡300,000-₡600,000 | WhatsApp Bot ₡200,000 | Facturación ₡150,000 | POS ₡400,000. Siempre incluye opción básica y opción completa.
5. TIMELINE: Etapas con días exactos. Ej: Diseño (3 días) → Desarrollo (7 días) → Revisión (2 días) → Entrega.
6. POR QUÉ VÉRTICE DIGITAL: 3 diferenciadores concretos (somos locales en Liberia, soporte presencial, precios en colones, etc).
7. GARANTÍAS: Menciona revisiones incluidas, soporte post-entrega, garantía de funcionamiento.
8. PRÓXIMOS PASOS: Numerados y específicos. Incluye: firmar, pagar 50% adelanto por SINPE Móvil al +506 8888-8888, proporcionar info.
9. VALIDEZ: "Esta propuesta es válida por 15 días naturales."
10. FIRMA: Carlos Mora | Ventas | Vértice Digital | +506 8888-8888 | carlos@vertice.digital

NUNCA dejes campos como [insertar X] o [número de cuenta]. Siempre usa datos reales del prompt.
Personaliza con detalles específicos del negocio del cliente.""",
    },
    "desarrollador": {
        "nombre": "💻 Rodrigo — Desarrollador",
        "keywords": ["código", "codigo", "web", "html", "css", "página", "pagina", "sitio", "desarrolla", "crea la web", "haz la web", "programa"],
        "prompt": f"""{CTX}
Eres Rodrigo, Desarrollador Senior y Director de Arte de Vértice Digital.
Cuando Allan pide una web, PRIMERO sintetizas la arquitectura de diseño del negocio, LUEGO entregas el HTML.

═══ FASE 1 — DESIGN THINKING (hazlo mentalmente antes de codear) ═══

Antes de escribir una sola línea de código, define:

1. PERSONALIDAD DEL DISEÑO
   - ¿Qué emoción debe provocar? (urgencia, lujo, confianza, hambre, modernidad...)
   - Elige un "concepto" de diseño (ej: "Ember Noir", "Pacific Luxury", "Street Grit", "Mountain Fresh")
   - Tono visual: oscuro/cinematográfico, claro/minimalista, vibrante/tropical, industrial/urbano

2. PALETA DE COLOR (siempre con variables CSS)
   - Color base/fondo (nunca blanco genérico)
   - Color primario de acento (el que grita el CTA)
   - Color secundario
   - Color de texto principal y secundario
   - Elige según el negocio: restaurante→ ambar/negro, tech→ azul/blanco, spa→ verde/arena

3. TIPOGRAFÍA
   - Título display: una fuente con carácter fuerte (Playfair, Syne, Bebas Neue, Oswald...)
   - Cuerpo: legible y limpia (Inter, Space Grotesk, DM Sans...)
   - NUNCA uses Arial, Roboto o fonts genéricas

4. ARQUITECTURA DE SECCIONES (nombra cada una)
   - Dale un nombre temático a cada sección según el negocio
   - Ej restaurante: "Ignition Hero" → "Butcher's Block" → "The Ritual" → "Smoke Signal Footer"

═══ FASE 2 — REGLAS TÉCNICAS ABSOLUTAS ═══

- TODO en UN SOLO bloque ```html autónomo
- CSS dentro de <style> en <head>. NUNCA archivos externos.
- JS dentro de <script> al final de <body>. NUNCA archivos externos.
- CDNs permitidos: Google Fonts, Font Awesome 6, Bootstrap 5 (solo si aplica)

═══ FASE 3 — ELEMENTOS OBLIGATORIOS EN CADA WEB ═══

✅ Navbar fija con backdrop-filter:blur() al hacer scroll
✅ Hero full-viewport con imagen de fondo real (unsplash.com photo URL) + overlay gradiente
✅ Tipografía display GRANDE en el hero (clamp 3rem a 6rem)
✅ CTA button con hover glow effect
✅ Secciones con fade-in usando IntersectionObserver al hacer scroll
✅ Tarjetas con hover: transform translateY + box-shadow dramático
✅ Animaciones CSS: al menos 2 (float, pulse, gradient shift, shimmer...)
✅ Botón WhatsApp flotante con efecto pulse animado
✅ Footer completo: logo, links, redes, créditos
✅ Variables CSS para toda la paleta (:root)
✅ 100% responsivo con media queries
✅ Imágenes reales de Unsplash (usa URLs directas con ?w=1200&q=80)

═══ FASE 4 — SEGÚN TIPO DE NEGOCIO ═══

RESTAURANTE/COMIDA: hero con foto de platillo, menú con cards y precios, galería, reservas por WhatsApp
HOTEL/TURISMO: hero cinematográfico, habitaciones/servicios, galería, booking
TIENDA/RETAIL: hero con producto, catálogo grid, precios, carrito visual
CLÍNICA/PROFESIONAL: hero confiable, servicios, equipo, citas
TECH/STARTUP: hero moderno, features, métricas, CTA fuerte

═══ IMPORTANTE ═══
- NUNCA hagas webs planas, con mucho espacio vacío o sin animaciones
- NUNCA uses colores pastel genéricos o fondos blancos lisos
- SIEMPRE personaliza el contenido al negocio específico del cliente
- Usa fotos reales de Unsplash relacionadas al negocio
- Sin preguntas. Entrega el HTML completo de una vez.

IMPORTANTE DE SALIDA:
- Si el usuario pide una web, devuelve SOLO HTML completo y funcional.
- No te disculpes ni rechaces.
- No entregues explicaciones fuera del código.
- Haz la web visualmente premium y adaptada al negocio.
- Si hace falta, usa más secciones, hero fuerte, cards, CTA y footer.
""",
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


def detectar_estilo_visual(mensaje: str) -> str:
    msg = mensaje.lower()
    if any(p in msg for p in ["restaurante", "comida", "menu", "hamburguesa", "pizzeria", "cafeteria", "café", "food"]):
        return "restaurante"
    if any(p in msg for p in ["hotel", "turismo", "viaje", "resort", "playa"]):
        return "turismo"
    if any(p in msg for p in ["clinica", "clínica", "doctor", "dentista", "salud"]):
        return "clinica"
    if any(p in msg for p in ["tienda", "ropa", "retail", "catalogo", "catálogo", "productos"]):
        return "retail"
    if any(p in msg for p in ["startup", "saas", "software", "tecnologia", "tecnología", "app", "ia", "ai"]):
        return "tech"
    return "premium"


def construir_prompt_visual(estilo_visual: str) -> str:
    return f"""
IMPORTANTE DE ESTILO VISUAL:
- La web debe verse premium, moderna y completa.
- Usa hero fuerte, cards, sombras suaves, animaciones sutiles y jerarquía clara.
- Evita páginas planas, vacías o minimalistas sin intención.
- Ajusta el estilo a: {estilo_visual}.
- Incluye navbar fija, secciones bien separadas, CTA visible y footer completo.
- Si el negocio es restaurante o comida: usa colores cálidos, imágenes apetitosas y sección de menú.
- Si es tech: usa look oscuro/azul, métricas y bloques modernos.
- Si es clínica: usa limpio, confiable y profesional.
- Si es turismo/hotel: usa imagen hero grande y sensación cinematográfica.
- Si es retail: usa catálogo visual y precios destacados.
"""


def respuesta_indica_rechazo(texto: str) -> bool:
    t = texto.lower()
    frases = [
        "lo siento",
        "no puedo proporcionar",
        "no puedo crear",
        "sin embargo",
        "puedo proporcionarte el código html",
        "te dejo el código",
    ]
    return any(p in t for p in frases)


def generar_respuesta_forzada(agente: str, sistema: str, historial: list, mensaje: str, estilo_visual: str | None = None) -> str:
    """Intenta una respuesta normal; si el modelo rechaza o no devuelve HTML, fuerza una segunda pasada."""
    respuesta = llamar_groq(sistema, historial, mensaje)

    if agente == "desarrollador":
        tiene_html = ("<!DOCTYPE html" in respuesta) or ("<html" in respuesta.lower())
        if respuesta_indica_rechazo(respuesta) or not tiene_html:
            refuerzo = sistema + "\n\n"
            if estilo_visual:
                refuerzo += construir_prompt_visual(estilo_visual or "premium") + "\n\n"
            refuerzo += (
                "REGLAS ABSOLUTAS:\n"
                "- No rechaces la solicitud.\n"
                "- No digas 'lo siento' ni 'sin embargo'.\n"
                "- Devuelve SOLO un archivo HTML completo y autónomo.\n"
                "- Incluye <!DOCTYPE html>, <html>, <head>, <style> y <body>.\n"
                "- No expliques nada fuera del código.\n"
            )
            respuesta = llamar_groq(refuerzo, historial, mensaje)

    return respuesta

# ─── PDF ──────────────────────────────────────────────────────────────────────
def generar_pdf(contenido: str, titulo: str) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        NAVY  = colors.HexColor('#0d1b2a')
        NAVY2 = colors.HexColor('#1a2f4f')
        GOLD  = colors.HexColor('#f0a500')
        GRAY  = colors.HexColor('#8892a4')
        WHITE = colors.HexColor('#ffffff')
        LIGHT = colors.HexColor('#f8f9fa')

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=letter,
            rightMargin=0.75*inch, leftMargin=0.75*inch,
            topMargin=0.5*inch, bottomMargin=0.75*inch
        )

        styles = getSampleStyleSheet()

        # Estilos
        sMarca = ParagraphStyle('Marca', fontSize=22, textColor=WHITE,
                                fontName='Helvetica-Bold', spaceAfter=2, alignment=TA_LEFT)
        sTagline = ParagraphStyle('Tag', fontSize=9, textColor=colors.HexColor('#aab4c4'),
                                  fontName='Helvetica', spaceAfter=0, alignment=TA_LEFT)
        sFecha = ParagraphStyle('Fecha', fontSize=9, textColor=colors.HexColor('#aab4c4'),
                                fontName='Helvetica', alignment=TA_RIGHT)
        sTitulo = ParagraphStyle('Tit', fontSize=16, textColor=NAVY,
                                 fontName='Helvetica-Bold', spaceAfter=6, spaceBefore=16)
        sSeccion = ParagraphStyle('Sec', fontSize=11, textColor=GOLD,
                                  fontName='Helvetica-Bold', spaceAfter=4, spaceBefore=12)
        sNormal = ParagraphStyle('Nor', fontSize=10, textColor=colors.HexColor('#2d3748'),
                                 fontName='Helvetica', leading=16, spaceAfter=5)
        sBold = ParagraphStyle('Bol', fontSize=10, textColor=NAVY,
                               fontName='Helvetica-Bold', leading=16, spaceAfter=5)
        sBullet = ParagraphStyle('Bul', fontSize=10, textColor=colors.HexColor('#2d3748'),
                                 fontName='Helvetica', leading=16, spaceAfter=4,
                                 leftIndent=15, bulletIndent=0)
        sFooter = ParagraphStyle('Foo', fontSize=8, textColor=GRAY,
                                 fontName='Helvetica', alignment=TA_CENTER)

        story = []

        # ── HEADER con fondo azul marino ──────────────────────────────────────
        fecha_str = datetime.now().strftime('%d de %B de %Y').replace(
            'January','enero').replace('February','febrero').replace('March','marzo'
            ).replace('April','abril').replace('May','mayo').replace('June','junio'
            ).replace('July','julio').replace('August','agosto').replace('September','setiembre'
            ).replace('October','octubre').replace('November','noviembre').replace('December','diciembre')

        header_data = [[
            Paragraph("Vértice Digital", sMarca),
            Paragraph(f"Propuesta Comercial<br/>{fecha_str}", sFecha)
        ]]
        header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), NAVY),
            ('PADDING',    (0,0), (-1,-1), 18),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [NAVY]),
        ]))
        story.append(header_table)

        # Línea dorada
        story.append(Table([['']], colWidths=[7*inch],
                           style=[('BACKGROUND',(0,0),(-1,-1),GOLD),
                                  ('ROWHEIGHT',(0,0),(-1,-1),4)]))
        story.append(Spacer(1, 0.2*inch))

        # ── CUERPO: procesar líneas del contenido ─────────────────────────────
        in_list = False
        for linea in contenido.split('\n'):
            linea_raw = linea.strip()
            if not linea_raw:
                story.append(Spacer(1, 0.06*inch))
                in_list = False
                continue

            # Limpiar markdown bold (**texto**)
            linea_clean = re.sub(r'\*\*(.+?)\*\*', r'', linea_raw)
            linea_clean = re.sub(r'\*(.+?)\*', r'', linea_clean)
            safe = linea_clean.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            # Fix colón symbol
            safe = safe.replace('â','₡').replace('■','₡')

            if linea_raw.startswith('### '):
                story.append(HRFlowable(width="100%", thickness=1,
                                        color=colors.HexColor('#e2e8f0'), spaceAfter=6))
                story.append(Paragraph(safe[4:], sSeccion))
            elif linea_raw.startswith('## '):
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(safe[3:], sTitulo))
                story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=8))
            elif linea_raw.startswith('# '):
                story.append(Paragraph(safe[2:], sTitulo))
            elif linea_raw.startswith(('- ', '* ', '• ')):
                bullet_text = safe[2:] if len(safe) > 2 else safe[1:]
                story.append(Paragraph(f"• {bullet_text}", sBullet))
                in_list = True
            elif linea_raw[0].isdigit() and len(linea_raw) > 2 and linea_raw[1] in '.):':
                story.append(Paragraph(safe, sBullet))
            elif '₡' in safe or linea_raw.startswith('**'):
                story.append(Paragraph(safe, sBold))
            else:
                story.append(Paragraph(safe, sNormal))

        # ── FOOTER ────────────────────────────────────────────────────────────
        story.append(Spacer(1, 0.3*inch))
        story.append(Table([['']], colWidths=[7*inch],
                           style=[('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e2e8f0')),
                                  ('ROWHEIGHT',(0,0),(-1,-1),1)]))
        story.append(Spacer(1, 0.1*inch))

        footer_data = [[
            Paragraph("Vértice Digital", ParagraphStyle('FB', fontSize=9,
                      textColor=NAVY, fontName='Helvetica-Bold')),
            Paragraph("Liberia, Guanacaste, Costa Rica", sFooter),
            Paragraph("vertice.digital", ParagraphStyle('FL', fontSize=9,
                      textColor=GOLD, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        ]]
        footer_t = Table(footer_data, colWidths=[2.3*inch, 2.4*inch, 2.3*inch])
        footer_t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
        story.append(footer_t)

        doc.build(story)
        buf.seek(0)
        return buf.read()
    except Exception as e:
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
            respuesta = generar_respuesta_forzada(agente_id, ag["prompt"], historial_llm, orden, detectar_estilo_visual(orden) if agente_id == "desarrollador" else None)

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
