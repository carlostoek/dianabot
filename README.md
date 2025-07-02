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


---

🚀 Instalación

1. Clona este repositorio:



git clone https://github.com/tuusuario/telegram_narrative_bot.git

2. Instala las dependencias:



pip install -r requirements.txt

3. Configura las variables en config.py:



DATABASE_URL = "postgresql://usuario:contraseña@host:puerto/dbname"
BOT_TOKEN = "TU_TOKEN_DE_TELEGRAM"
ADMIN_USER_IDS = [123456789]  # IDs de los administradores

4. Inicializa la base de datos:



python database_init.py

5. Ejecuta el bot:



python main.py


---

🗂️ Desarrollo por Fases

El proyecto se desarrolla de manera modular y secuencial por fases.

Fase	Descripción	Módulos Involucrados

1	Infraestructura base, onboarding y mochila	User, UserBackpack, LorePiece
2	Combinación de piezas y acceso VIP	LorePiece, VIPAccess, VIPToken
3	Notificaciones Lucien y Mayordomo	Notification
4	Gamificación (misiones, recompensas, minijuegos)	Mission, UserMission, DailyGift
5	Panel administrativo	AdminSettings, BotConfiguration
6	Automatización y optimización	SystemTask


Cada fase debe ser completamente funcional antes de avanzar a la siguiente.


---

⚙️ Tecnologías Utilizadas

Python 3.10+

Aiogram 3.x (Telegram Bot Framework)

SQLAlchemy ORM

APScheduler (tareas programadas)

PostgreSQL (Base de datos recomendada)

Docker (opcional para despliegue)

Railway.app (opcional para hosting)



---

🛠️ Funcionalidades Principales

Registro y onboarding automático con personajes.

Sistema de mochila con coleccionables de narrativa.

Combinación de pistas para desbloquear contenido especial.

Acceso VIP con suscripciones controladas.

Notificaciones aleatorias y personalizadas.

Misiones diarias, recompensas y minijuegos.

Menú administrativo completo.

Tareas programadas automatizadas.



---

✅ Estado del Proyecto

🔨 En desarrollo por fases.
✔️ Estructura base finalizada.
✔️ Diseño integral y arquitectura completados.
🚀 Listo para implementación secuencial.


---

📧 Contacto

Desarrollado por: [Tu Nombre]
Contacto: [tuemail@ejemplo.com]
Telegram: [@tu_usuario]


---

📝 Licencia

Este proyecto se distribuye bajo la licencia MIT.
Consulta el archivo LICENSE para más información.
