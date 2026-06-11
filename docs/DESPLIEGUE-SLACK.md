# Despliegue del bot de Slack

El bot corre en **Socket Mode**: se conecta él hacia Slack, así que no necesita
URL pública, dominio ni puertos abiertos. Puede correr en el VPS, en un PC que
quede encendido, o donde sea que haya Python e internet.

## 1. Crear la Slack app (5 minutos, una sola vez)

1. Entrar a <https://api.slack.com/apps> → **Create New App** → **From a manifest**.
2. Elegir el workspace (el de Teilur, o uno propio para probar primero).
3. Borrar todo lo que traiga el editor y pegar el manifest, según el formato que pida el editor (hay un toggle YAML/JSON arriba):
   - **JSON** (lo que suele venir por defecto): pegar [deploy/slack-app-manifest.json](../deploy/slack-app-manifest.json).
   - **YAML**: pegar [deploy/slack-app-manifest.yaml](../deploy/slack-app-manifest.yaml).
   - Luego **Next** → **Create**.
4. En **Settings → Basic Information → App-Level Tokens** → **Generate Token and Scopes**:
   - Nombre: `socket-mode`
   - Scope: `connections:write`
   - Copiar el token que empieza con `xapp-` → es el `SLACK_APP_TOKEN`.
5. En **Settings → Install App** → **Install to Workspace** → autorizar.
   - Copiar el **Bot User OAuth Token** que empieza con `xoxb-` → es el `SLACK_BOT_TOKEN`.
6. En **Features → App Home → Show Tabs**, activar **Messages Tab** y marcar
   **"Allow users to send Slash commands and messages from the messages tab"**.
   Sin esto, Slack muestra "Se ha desactivado el envío de mensajes a esta aplicación"
   y no deja escribirle por DM. (El manifest ya lo trae activado; este paso solo
   aplica si la app se creó antes de incluirlo o se configuró a mano.)

> Nota: instalar apps en el workspace de Teilur puede requerir aprobación de un
> admin. Si hay fricción, probar primero en un workspace propio gratuito.

## 2. Configurar y arrancar

En la máquina donde va a correr:

```bash
git clone https://github.com/Teilur-Engineering/Auditor-blogs.git
cd Auditor-blogs
python -m venv .venv
source .venv/bin/activate        # Linux  (Windows: .venv\Scripts\activate)
pip install -e .
cp .env.example .env             # completar OPENAI_API_KEY, SLACK_BOT_TOKEN, SLACK_APP_TOKEN
blog-auditor slack
```

Si arranca bien se ve `⚡️ Bolt app is running!` en el log.

## 3. Cómo se usa desde Slack

Por **DM al bot** o **mencionándolo** (`@blog-auditor`) en un canal donde esté:

- Pegar el link de un Google Doc compartido como "cualquiera con el enlace puede ver".
- O adjuntar el borrador como `.docx`, `.pdf`, `.md` o `.txt`.
- O pegar el texto del borrador directo en el mensaje.
- Opcional: agregar `keyword: la keyword objetivo` en el mismo mensaje.

El bot responde en el hilo: primero "revisando…", luego el resumen con puntajes
y al final el reporte completo adjunto como archivo Markdown.

## 4. Dejarlo corriendo permanente (VPS Linux con systemd)

Crear `/etc/systemd/system/blog-auditor.service`:

```ini
[Unit]
Description=Blog Auditor - bot de Slack de revision de blogs
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=blogauditor
WorkingDirectory=/opt/Auditor-blogs
ExecStart=/opt/Auditor-blogs/.venv/bin/blog-auditor slack
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now blog-auditor
sudo systemctl status blog-auditor        # verificar
journalctl -u blog-auditor -f             # logs en vivo
```

> Recomendación: crear un usuario sin privilegios (`blogauditor`) para el
> servicio y dejar el `.env` con permisos `600`.

## 5. Solución de problemas

| Síntoma | Causa probable |
|---|---|
| `Error: Faltan SLACK_BOT_TOKEN...` | El `.env` no tiene los tokens o está en otra carpeta (el bot lee el `.env` del directorio desde donde se ejecuta). |
| `invalid_auth` al arrancar | El `SLACK_BOT_TOKEN` está mal copiado o la app no está instalada en el workspace. |
| El bot no responde DMs | Falta el evento `message.im` o el scope `im:history` (recrear la app desde el manifest). |
| No puede descargar adjuntos | Falta el scope `files:read`, o el bot no está en el canal donde se subió el archivo. |
| Responde pero la revisión falla | Revisar `OPENAI_API_KEY` y saldo de la cuenta de OpenAI. |
