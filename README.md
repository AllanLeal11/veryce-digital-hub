# Vértice AI Hub v2 — Panel CEO

## Variables de entorno en Railway

| Variable | Obligatoria | Descripción |
|---|---|---|
| `GROQ_API_KEY` | ✅ Sí | Tu clave de Groq |
| `NETLIFY_TOKEN` | ✅ Para deploy | Personal Access Token de Netlify |
| `NETLIFY_SITE_ID` | ❌ Opcional | ID de sitio existente en Netlify |

## Cómo obtener el NETLIFY_TOKEN
1. Ve a https://app.netlify.com/user/applications
2. Personal access tokens → New access token
3. Copia el token y pégalo en Railway → Variables

## Flujo de uso
1. Allan escribe una orden (ej: "hazme una web para un restaurante en Liberia")
2. El sistema detecta el agente correcto automáticamente
3. El agente entrega el resultado inmediatamente
4. Si hay HTML → botón para descargar o hacer deploy a Netlify
5. Si es propuesta/cotización → botón para descargar PDF
