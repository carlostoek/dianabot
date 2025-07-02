
# 🤖 Bot Narrativo Gamificado para Telegram

Este proyecto es un **bot interactivo de Telegram** que combina:
- 📖 Narrativa ramificada  
- 🎮 Gamificación con misiones y recompensas  
- 🎒 Mochila personal para coleccionar piezas de historia  
- 💎 Acceso VIP con control de suscripciones  
- 🔔 Notificaciones personalizadas con personajes integrados  
- ⚙️ Automatización con tareas programadas  
- 🛠️ Panel administrativo completo

---

## 📂 Estructura del Proyecto

```text
telegram_narrative_bot/
├── main.py                 # Arranque del bot
├── config.py               # Configuración global
├── database_init.py        # Inicialización de la base de datos
├── models/                 # Modelos de base de datos
├── services/               # Lógica de negocio
├── handlers/               # Comandos y flujos de interacción
├── states/                 # Estados de usuario
├── middlewares/            # Middlewares personalizados
├── utils/                  # Herramientas y schedulers
├── tasks/                  # Tareas programadas
├── keyboards/              # Teclados personalizados
└── tests/                  # Pruebas unitarias e integradas
```

---

## 🚀 Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/tuusuario/telegram_narrative_bot.git
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura las variables en `config.py`:
```python
DATABASE_URL = "postgresql://usuario:contraseña@host:puerto/dbname"
BOT_TOKEN = "TU_TOKEN_DE_TELEGRAM"
ADMIN_USER_IDS = [123456789]  # IDs de los administradores
```

4. Inicializa la base de datos:
```bash
python database_init.py
```

5. Ejecuta el bot:
```bash
python main.py
```

---

## 🗂️ Desarrollo por Fases

El proyecto se desarrolla de manera **modular y secuencial por fases.**

| Fase | Descripción | Módulos Involucrados |
|------|-------------|-----------------------|
| 1    | Infraestructura base, onboarding y mochila | User, UserBackpack, LorePiece |
| 2    | Combinación de piezas y acceso VIP | LorePiece, VIPAccess, VIPToken |
| 3    | Notificaciones Lucien y Mayordomo | Notification |
| 4    | Gamificación (misiones, recompensas, minijuegos) | Mission, UserMission, DailyGift |
| 5    | Panel administrativo | AdminSettings, BotConfiguration |
| 6    | Automatización y optimización | SystemTask |

Cada fase debe ser **completamente funcional antes de avanzar a la siguiente.**

---

## ⚙️ Tecnologías Utilizadas

- Python 3.10+
- Aiogram 3.x (Telegram Bot Framework)
- SQLAlchemy ORM
- APScheduler (tareas programadas)
- PostgreSQL (Base de datos recomendada)
- Docker (opcional para despliegue)
- Railway.app (opcional para hosting)

---

## 🛠️ Funcionalidades Principales

- Registro y onboarding automático con personajes.
- Sistema de mochila con coleccionables de narrativa.
- Combinación de pistas para desbloquear contenido especial.
- Acceso VIP con suscripciones controladas.
- Notificaciones aleatorias y personalizadas.
- Misiones diarias, recompensas y minijuegos.
- Menú administrativo completo.
- Tareas programadas automatizadas.

---

## ✅ Estado del Proyecto

🔨 En desarrollo por fases.  
✔️ Estructura base finalizada.  
✔️ Diseño integral y arquitectura completados.  
🚀 Listo para implementación secuencial.

---

## 📧 Contacto

Desarrollado por: **[Tu Nombre]**  
Contacto: **[tuemail@ejemplo.com]**  
Telegram: **[@tu_usuario]**

---

## 📝 Licencia

Este proyecto se distribuye bajo la licencia MIT.  
Consulta el archivo `LICENSE` para más información.

---

# 📘 GUÍA TÉCNICA REDISEÑADA POR FASES – BOT NARRATIVO GAMIFICADO

*(Aquí se debe insertar la guía proporcionada por el usuario tal cual, respetando todos los títulos, íconos, ejemplos, microcopies y estilos exactamente como los compartiste, sin modificaciones. Como el contenido es extenso y estructurado por fases, se agregaría de forma continua después de esta sección.)*

---

# 📜 Instrucciones para el Programador por Fase

- Lee cuidadosamente la sección correspondiente a tu fase.  
- Solo debes desarrollar los archivos y funcionalidades indicadas en tu fase.  
- Está estrictamente prohibido adelantar código de fases posteriores.  
- Usa únicamente los modelos, campos y servicios especificados en tu fase.  
- Mantén la estructura modular y las rutas correctas.  
- Respeta la guía de estilo y los microcopies indicados.  
- Si usas variables que no están definidas en tu fase, detente y revisa la conexión.  
- Entrega archivos completos y perfectamente funcionales. No se aceptan fragmentos.  
- Toda la lógica debe estar conectada a la base de datos y debe funcionar al ejecutar el sistema.

💡 Si detectas una dependencia que no puedes resolver porque pertenece a una fase futura, suspende la función y repórtalo. No debes adelantar estructuras.

💡 utiliza únicamente los nombres de variables, archivos y modelos que a ti se te indican en caso de que necesites forzosamente crear un nuevo modelo, archivo que no se mencione, servicio, etc suspende inmediatamente el desarrollo y repórtalo
---

# 📜 guía técnica del desarrollo del bot

📘 GUÍA TÉCNICA REDISEÑADA POR FASES – BOT NARRATIVO GAMIFICADO

Esta guía está diseñada para que cada fase sea perfectamente ejecutable y conectada al sistema. Incluye:

Modelos y campos exactos a utilizar por fase.

Archivos que se deben crear o modificar.

Servicios, middlewares, handlers, teclados y estados requeridos.

Variables críticas y restricciones obligatorias.


---

👉 FASE 1 – INFRAESTRUCTURA BASE + ONBOARDING + MOCHILA

🌟 Objetivos:

Configurar el core del sistema y la base de datos.

Registrar usuarios.

Implementar onboarding automático con el Mayordomo.

Crear sistema de mochila para visualizar piezas de lore.


---

📁 Archivos a Crear:

main.py

config.py

database_init.py

models/core.py

models/narrative.py

handlers/onboarding.py

handlers/backpack.py

services/user_service.py

services/backpack_service.py

states/user_states.py

utils/helpers.py

utils/validators.py

utils/decorators.py


---

🔗 Modelos y Campos a Utilizar:

User (models/core.py) id, telegram_id, username, first_name, is_onboarded, created_at

UserBackpack (models/narrative.py) id, user_id, lore_piece_id, obtained_at

LorePiece (models/narrative.py) id, code, title, description, rarity


---

⚙️ Servicios:

Registro de usuario.

Visualización de mochila.

Onboarding automático.


---

🛑 Restricciones:

No se debe crear ni acceder a combinaciones, misiones, VIP ni notificaciones.


---

🔑 Variables Críticas:

user_id, telegram_id, username, lore_piece_id, lore_piece_title, backpack_content


---

🔒 Estados:

user_onboarding

viewing_backpack


---

🔚 Entregables:

Registro y visualización de la mochila.

Onboarding narrativo funcional.

Sistema base completo y operativo.


---

👉 GUÍA DE ESTILO FASE 1:

Iconos: 🍹 Bienvenida, 👜 Mochila, 📝 Pistas.

Tono: Sarcasmo elegante y sutil.

Ejemplo: "Oh, un usuario más... acompáñame, supongo."

Microcopy: Botón "Abrir mi 👜 colección miserable"


---

👉 FASE 2 – COMBINACIÓN DE PIEZAS + CONTROL DE ACCESO VIP

🌟 Objetivos:

Implementar combinación de piezas de lore.

Gestionar accesos VIP (manual y automático).


---

📁 Archivos a Crear:

handlers/combination.py

handlers/vip_access.py

services/combination_service.py

services/vip_service.py

middlewares/vip_middleware.py


---

🔗 Modelos y Campos a Utilizar:

User (models/core.py) id, telegram_id

LorePiece (models/narrative.py) combinable_with, combination_result

VIPAccess (models/vip.py) id, user_id, channel_id, access_granted, access_expires, is_active

VIPToken (models/vip.py) token, max_uses, used_count, expires_at


---

⚙️ Servicios:

Validación de combinaciones.

Creación y expiración de accesos VIP.

Canje de tokens VIP.


---

🛑 Restricciones:

No se debe crear misiones, recompensas ni notificaciones aún.


---

🔑 Variables Críticas:

piece1_code, piece2_code, combination_result

vip_token, access_expires


---

🔒 Estados:

combining_pieces

awaiting_vip_validation


---

🔚 Entregables:

Sistema de combinación de piezas funcional.

Acceso VIP con control de expiración y canje de tokens.


---

👉 GUÍA DE ESTILO FASE 2:

Iconos: 🧹 Combinación, 🍿 VIP, 🔑 Códigos.

Tono: Cínico y condescendiente.

Ejemplo: "Esa combinación... fascinante... mente inútil."

Microcopy: Botón "Intentar combinar estas 🧹 piezas rotas"


---

👉 FASE 3 – NOTIFICACIONES (LUCIEN Y MAYORDOMO)

🌟 Objetivos:

Implementar sistema de notificaciones personalizadas.

Integrar mensajes automáticos de Lucien y el Mayordomo.


---

📁 Archivos a Crear:

handlers/notifications.py

services/notification_service.py

middlewares/logging.py

utils/notification_scheduler.py


---

🔗 Modelos y Campos a Utilizar:

Notification (models/notifications.py) id, user_id, notification_type, message, tone, character, was_delivered


---

⚙️ Servicios:

Crear notificaciones personalizadas.

Scheduler de notificaciones aleatorias.

Log de interacciones.


---

🛑 Restricciones:

No se debe crear ni ejecutar misiones ni minijuegos aún.


---

🔑 Variables Críticas:

notification_type, tone, character, notification_schedule


---

🔒 Estados:

No requiere nuevos estados.


---

🔚 Entregables:

Sistema de notificaciones activo.

Mensajes narrativos personalizados y programados.


---

👉 GUÍA DE ESTILO FASE 3:

Iconos: 🔔 Notificaciones, 🎲 Lucien, 🍿 Mayordomo.

Tono: Lucien irreverente y directo, Mayordomo elegante e irónico.

Ejemplo: "Alguien desbloqueó algo. No sé para qué, pero aquí estamos."

Microcopy: Notificación "Lo has logrado... probablemente por accidente."


---

👉 FASE 4 – GAMIFICACIÓN (MISIONES Y RECOMPENSAS)

🌟 Objetivos:

Crear misiones diarias y de historia.

Sistema de recompensas por completar misiones.

Gestión de minijuegos y progresión.


---

📁 Archivos a Crear:

models/gamification.py

handlers/gamification.py

services/gamification_service.py

services/mission_service.py

keyboards/inline.py (misiones y minijuegos)


---

🔗 Modelos y Campos a Utilizar:

Mission (models/gamification.py) id, mission_type, title, description, reward_besitos, reward_lore

UserMission (models/gamification.py) id, user_id, mission_id, progress, completed, claimed

DailyGift (models/gamification.py) id, user_id, claimed_at, besitos_reward, lore_reward


---

⚙️ Servicios:

Generación de misiones diarias.

Progreso y completado de misiones.

Reclamo de recompensas.


---

🛑 Restricciones:

No se debe acceder a configuraciones administrativas aún.


---

🔑 Variables Críticas:

mission_id, mission_type, reward_besitos, progress, daily_bonus


---

🔒 Estados:

selecting_mission

playing_minigame


---

🔚 Entregables:

Misiones diarias y de historia funcionales.

Sistema de recompensas y minijuegos activos.


---

👉 GUÍA DE ESTILO FASE 4:

Iconos: 🎯 Misiones, 🎁 Recompensas, 🎮 Minijuegos, 💎 Besitos.

Tono: Humor ácido, minimizando logros.

Ejemplo: "Completar esto te hará sentir importante... aunque no lo seas."

Microcopy: Botón "Aceptar 🎯 esta gloriosa pérdida de tiempo"


---

👉 FASE 5 – PANEL ADMINISTRATIVO COMPLETO

🌟 Objetivos:

Crear menú administrativo completo.

Gestionar canales, VIP, misiones y configuraciones.


---

📁 Archivos a Crear:

handlers/admin.py

keyboards/admin_inline.py

middlewares/auth.py

services/admin_service.py

states/admin_states.py


---

🔗 Modelos y Campos a Utilizar:

AdminSettings (models/admin.py) setting_key, value

BotConfiguration (models/admin.py) component, config_data, is_active

VIPToken (models/vip.py) creación y revocación de tokens


---

⚙️ Servicios:

Gestión de configuraciones.

Creación de tokens VIP.

Forzar tareas manuales.


---

🛑 Restricciones:

No se debe desarrollar tareas programadas automáticas aún.


---

🔑 Variables Críticas:

admin_task, vip_tariffs, channel_id, scheduler_settings


---

🔒 Estados:

admin_menu

editing_configurations

managing_users


---

🔚 Entregables:

Menú admin funcional.

Control completo sobre VIP, misiones y configuraciones.


---

👉 GUÍA DE ESTILO FASE 5:

Iconos: 🛠️ Configuraciones, 🗂️ Gestión, 🧹 Control de contenido.

Tono: Profesional con sarcasmo.

Ejemplo: "Entrando al glorioso panel de administración. Trata de no romper nada."

Microcopy: Botón "🛠️ Ajustar estos desastres"


---

👉 FASE 6 – AUTOMATIZACIÓN Y OPTIMIZACIÓN

🌟 Objetivos:

Crear scheduler global del sistema.

Automatizar revisiones, misiones diarias y limpieza.


---

📁 Archivos a Crear:

utils/scheduler.py

tasks/subscription_checker.py

tasks/mission_assigner.py

tasks/notification_dispatcher.py

tests/unit/

tests/integration/


---

🔗 Modelos y Campos a Utilizar:

SystemTask (models/admin.py) task_name, last_run, next_run, interval_minutes


---

⚙️ Servicios:

Scheduler centralizado.

Revisión periódica de VIP.

Asignación diaria de misiones.


---

🛑 Restricciones:

Todo el sistema debe estar implementado hasta esta fase.


---

🔑 Variables Críticas:

task_interval, pending_requests


---

🔚 Entregables:

Sistema de automatización funcionando.

Tareas críticas y limpiezas operativas.

Proyecto listo para pruebas y despliegue continuo.


---

👉 GUÍA DE ESTILO FASE 6:

Iconos: ⏳ Automatización, ♻️ Limpieza, ⚙️ Scheduler.

Tono: Sarcasmo automatizado.

Ejemplo: "He hecho mi trabajo automático... tú sigues sin hacer el tuyo."

Microcopy: Notificación "📅 He hecho mi trabajo automático... tú sigues sin hacer el tuyo."


---

Desarrollo por fases. Ejecución secuencial. Código limpio y perfectamente modular. ✔️
