# Acento Redes - OpenClaw + WhatsApp

Integracion de [OpenClaw](https://openclaw.ai/) con WhatsApp para Acento Redes. OpenClaw es un asistente de IA personal open-source que se conecta directamente con WhatsApp mediante la libreria Baileys.

## Requisitos

- **Node.js 22+** (recomendado Node 24)
- **npm** o **pnpm**
- **API Key** de Anthropic (Claude) u OpenAI
- **Telefono con WhatsApp** para vincular el bot

## Inicio Rapido

### Opcion 1: Setup automatizado (recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/cristianverbel/acentoredes.git
cd acentoredes

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu API key

# 3. Ejecutar setup
./setup.sh
```

El script te guiara paso a paso: instala OpenClaw, configura WhatsApp y arranca el gateway.

### Opcion 2: Docker Compose

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu API key

# 2. Levantar el servicio
docker compose up -d

# 3. Vincular WhatsApp (escanear QR)
docker exec -it acentoredes-openclaw openclaw channels login --channel whatsapp
```

### Opcion 3: Instalacion manual

```bash
# 1. Instalar OpenClaw
npm install -g openclaw@latest

# 2. Configuracion inicial
openclaw onboard --install-daemon

# 3. Instalar plugin de WhatsApp
openclaw plugins install @openclaw/whatsapp

# 4. Copiar configuracion
cp openclaw.config.yaml ~/.openclaw/config.yaml

# 5. Vincular WhatsApp (escanear codigo QR)
openclaw channels login --channel whatsapp

# 6. Iniciar el gateway
openclaw gateway --port 18789 --verbose
```

## Configuracion

### Variables de entorno (.env)

| Variable | Descripcion | Requerida |
|----------|-------------|-----------|
| `ANTHROPIC_API_KEY` | API key de Anthropic (Claude) | Si* |
| `OPENAI_API_KEY` | API key de OpenAI | Si* |
| `OPENCLAW_MODEL_PROVIDER` | Proveedor: `anthropic`, `openai`, `deepseek` | No (default: anthropic) |
| `GATEWAY_PORT` | Puerto del gateway | No (default: 18789) |

\* Al menos una API key es requerida segun el proveedor elegido.

### Configuracion de WhatsApp (openclaw.config.yaml)

Las opciones principales estan en la seccion `channels.whatsapp`:

- **`dmPolicy`**: Controla quien puede enviar mensajes directos
  - `pairing` - Requiere codigo de emparejamiento (recomendado)
  - `allowlist` - Solo numeros en la lista
  - `open` - Cualquiera puede escribir
  - `disabled` - DMs deshabilitados

- **`allowFrom`**: Lista de numeros permitidos en formato E.164
  ```yaml
  allowFrom:
    - "+573001234567"  # Colombia
    - "+521234567890"  # Mexico
  ```

- **`groupPolicy`**: Controla acceso en grupos (`disabled`, `allowlist`, `open`)

- **`reactionLevel`**: Reacciones con emoji (`off`, `ack`, `minimal`, `extensive`)

## Uso

Una vez configurado y con el gateway corriendo, envia un mensaje de WhatsApp al numero vinculado y OpenClaw respondera automaticamente.

### Comandos utiles

```bash
# Ver estado del bot
openclaw doctor

# Listar solicitudes de emparejamiento pendientes
openclaw pairing list whatsapp

# Aprobar un emparejamiento
openclaw pairing approve whatsapp <CODIGO>

# Enviar mensaje desde la terminal
openclaw message send --to "+573001234567" --message "Hola desde Acento Redes"

# Ejecutar agente con tarea especifica
openclaw agent --message "Responde las preguntas frecuentes" --thinking high
```

### Logs y monitoreo

```bash
# Ver logs del gateway
openclaw gateway --verbose

# Con Docker
docker compose logs -f openclaw
```

## Notas Importantes

- **Telefono activo**: Tu telefono debe permanecer conectado a internet. Si se desconecta por mas de ~14 dias, WhatsApp desvinculara la sesion.
- **Numero dedicado**: Se recomienda usar un numero de telefono exclusivo para el bot, separado de tu numero personal.
- **Credenciales**: Las credenciales de WhatsApp se guardan en `~/.openclaw/credentials/whatsapp/`.
- **Seguridad**: Nunca compartas tu archivo `.env` ni las credenciales de WhatsApp.

## Estructura del Proyecto

```
acentoredes/
├── docker-compose.yml      # Configuracion de Docker
├── openclaw.config.yaml    # Configuracion de OpenClaw y WhatsApp
├── setup.sh                # Script de instalacion automatizada
├── .env.example            # Template de variables de entorno
├── .gitignore              # Archivos excluidos de git
└── README.md               # Esta documentacion
```

## Recursos

- [Documentacion oficial de OpenClaw](https://docs.openclaw.ai)
- [Guia de WhatsApp de OpenClaw](https://docs.openclaw.ai/channels/whatsapp)
- [Repositorio de OpenClaw en GitHub](https://github.com/openclaw/openclaw)
