import logging
import random
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# CONFIGURACIÓN GOOGLE SHEETS
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
client = gspread.authorize(creds)
sheet = SHEET_ID = "1zyJ4yYBauBQuPoZvEEpuZRb-TB9pTHwlxi4H31nGVr0"
sheet = client.open_by_key(SHEET_ID).worksheet("Es la que va")


# TOKEN DEL BOT
TOKEN = "8175423867:AAHnExwL5nwVsuKdvWfKkxAs7ZauJAADWDM"

usuarios = {}
favoritos = {}

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
CATEGORIAS = ["desayuno", "almuerzo", "merienda", "cena", "Catering", "Ensalada", "Guarnición", "Postre"]

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola mi reina! Decime qué querés comer hoy: desayuno, almuerzo, merienda o cena.")

# MENSAJE
async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text.lower().strip()

    # Saludos
    saludos = ["hola", "holaa", "buen día", "buen dia", "buenas", "buenas tardes", "buenas noches"]
    if texto in saludos:
        hora = datetime.now().hour
        if hora < 12:
            saludo = "¡Buen día, reina! ☀️"
        elif 12 <= hora < 19:
            saludo = "¡Buenas tardes, reina! ☕️"
        else:
            saludo = "¡Buenas noches, reina! 🌙"
        await update.message.reply_text(f"{saludo} ¿Qué comemos hoy?")
        return

    # Despedidas
    despedidas = ["chau", "chao", "gracias", "nos vemos", "adios", "adiós", "hasta luego", "hasta mañana"]
    if texto in despedidas:
        await update.message.reply_text("De nada mi reina, fue un placer cocinar para vos hoy 🍽️❤️")
        return

    # SORPRENDEME
    if texto == "sorprendeme":
        datos = sheet.get_all_records()
        if datos:
            receta = random.choice(datos)
            usuarios[user_id] = {"ultima": receta}
            await update.message.reply_text("✨ Modo antojo activado ✨", parse_mode="Markdown")
            await update.message.reply_text(formatear_respuesta(receta), parse_mode="Markdown")
        else:
            await update.message.reply_text("No encontré recetas 😥")
        return

    # OTRA
    if texto == "otra":
        if user_id in usuarios and usuarios[user_id].get("opciones"):
            receta = usuarios[user_id]["opciones"].pop()
            usuarios[user_id]["ultima"] = receta
            await update.message.reply_text(formatear_respuesta(receta), parse_mode="Markdown")
        else:
            await update.message.reply_text("No tengo más opciones 😥. Probá con otra categoría.")
        return

    # FAVORITOS
    if texto in ["me encantó", "guardalo", "favorito"]:
        if user_id in usuarios and "ultima" in usuarios[user_id]:
            receta = usuarios[user_id]["ultima"]
            favoritos.setdefault(user_id, []).append(receta)
            await update.message.reply_text("Guardada como favorita, reina ✨⭐")
        else:
            await update.message.reply_text("Todavía no me dijiste qué receta te gustó 😅")
        return

    if texto == "ver favoritos":
        if user_id in favoritos and favoritos[user_id]:
            await update.message.reply_text("Tus favoritas, mi reina 👑:")
            for receta in favoritos[user_id]:
                await update.message.reply_text(formatear_respuesta(receta), parse_mode="Markdown")
        else:
            await update.message.reply_text("Todavía no guardaste ninguna receta 😢")
        return

    # MENÚ SEMANAL
    if "menu semanal" in texto or "menú semanal" in texto or "quiero que me armes" in texto:
        datos = sheet.get_all_records()
        clave_categoria = next((k for k in datos[0].keys() if "categoría" in k.lower()), None)
        if not clave_categoria:
            await update.message.reply_text("Error: no encontré la columna 'Categoría'.")
            return

        menu = {}
        for dia in DIAS:
            menu[dia] = {}
            for cat in CATEGORIAS:
                opciones = [f for f in datos if f[clave_categoria].lower() == cat]
                if opciones:
                    menu[dia][cat] = random.choice(opciones)
        usuarios[user_id]["menu"] = menu

        mensaje_menu = "*📅 Menú Semanal Morfandobot*\n\n"
        for dia in DIAS:
            mensaje_menu += f"*{dia}*\n"
            for cat in CATEGORIAS:
                if cat in menu[dia]:
                    mensaje_menu += f"{emoji_categoria(cat)} *{cat.capitalize()}:* {menu[dia][cat]['Nombre']}\n"
            mensaje_menu += "\n"

        await update.message.reply_text(mensaje_menu, parse_mode="Markdown")
        return

    # RECETAS POR CATEGORÍA
    datos = sheet.get_all_records()
    clave_categoria = next((k for k in datos[0].keys() if "categoría" in k.lower()), None)
    if not clave_categoria:
        await update.message.reply_text("Error: la columna 'Categoría' no fue encontrada. Revisá el nombre exacto en la hoja.")
        return

    opciones = [fila for fila in datos if fila[clave_categoria].lower() == texto]

    if opciones:
        random.shuffle(opciones)
        primera = opciones.pop()
        usuarios[user_id] = {"categoria": texto, "opciones": opciones, "ultima": primera}
        await update.message.reply_text(formatear_respuesta(primera), parse_mode="Markdown")
        await update.message.reply_text("❤️ De nada mi reina, ¡espero haberte ayudado y que te salga riquísimo!")
    else:
        await update.message.reply_text("No encontré recetas en esa categoría 😅 Probá con: desayuno, almuerzo, merienda o cena.")

# FORMATEO
def formatear_respuesta(receta):
    return (
        f"🍽️ *{receta['Nombre']}*\n\n"
        f"🧂 *Ingredientes:*\n{receta['Ingredientes']}\n\n"
        f"👩‍🍳 *Preparación:*\n{receta['Preparación']}"
    )

def emoji_categoria(cat):
    return {
        "desayuno": "🍳",
        "almuerzo": "🥗",
        "merienda": "☕️",
        "cena": "🍝"
    }.get(cat, "🍽️")

# INICIO
logging.basicConfig(level=logging.INFO)
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))

print("Bot activo 🔥")
app.run_polling()
