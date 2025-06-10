# bot.py

import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from calculator import calculate_montage_price

logging.basicConfig(level=logging.INFO)

# Состояния диалога
(
    TYPING_EQUIP_COST,
    ASK_MACHINE_ROOM,
    ASK_SHAFT_TYPE,
    ASK_REPLACEMENT,
    ASK_DOORS,
    ASK_PLATFORMS,
    ASK_DISPATCHER,
    ASK_REGION
) = range(8)

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите стоимость оборудования в рублях:")
    return TYPING_EQUIP_COST

async def equipment_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.replace(' ', '').replace(',', '.'))
        user_data[update.message.chat_id] = {"price": price}
        reply = ReplyKeyboardMarkup([["Да", "Нет"]], one_time_keyboard=True)
        await update.message.reply_text("Есть машинное помещение?", reply_markup=reply)
        return ASK_MACHINE_ROOM
    except:
        await update.message.reply_text("Введите число. Например: 950000")
        return TYPING_EQUIP_COST

async def machine_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id]["no_machine_room"] = (update.message.text == "Нет")
    reply = ReplyKeyboardMarkup([["монолит", "металлическая", "кирпичная"]], one_time_keyboard=True)
    await update.message.reply_text("Тип шахты?", reply_markup=reply)
    return ASK_SHAFT_TYPE

async def shaft_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id]["shaft_type"] = update.message.text
    reply = ReplyKeyboardMarkup([["Замена", "Новостройка"]], one_time_keyboard=True)
    await update.message.reply_text("Тип объекта?", reply_markup=reply)
    return ASK_REPLACEMENT

async def replacement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id]["replacement"] = (update.message.text == "Замена")
    reply = ReplyKeyboardMarkup([["Да", "Нет"]], one_time_keyboard=True)
    await update.message.reply_text("Кабина проходная? (дверей больше, чем остановок)", reply_markup=reply)
    return ASK_DOORS

async def doors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id]["more_doors"] = (update.message.text == "Да")
    reply = ReplyKeyboardMarkup([["Мы", "Застройщик"]], one_time_keyboard=True)
    await update.message.reply_text("Кто делает настилы?", reply_markup=reply)
    return ASK_PLATFORMS

async def platforms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id]["we_do_platforms"] = (update.message.text == "Мы")
    reply = ReplyKeyboardMarkup([["Базовая", "IP", "Без диспетчеризации"]], one_time_keyboard=True)
    await update.message.reply_text("Тип диспетчеризации?", reply_markup=reply)
    return ASK_DISPATCHER

async def dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id]["dispatcher"] = update.message.text
    reply = ReplyKeyboardMarkup([["СПб", "Регион"]], one_time_keyboard=True)
    await update.message.reply_text("Где находится объект?", reply_markup=reply)
    return ASK_REGION

async def region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id]["region"] = (update.message.text == "Регион")

    params = user_data[update.message.chat_id]
    price = params.pop("price")

    result = calculate_montage_price(price, params)

    breakdown = "\n".join(
        f"{label}: +{int(minv):,} — +{int(maxv):,} ₽" for label, minv, maxv in result["adjustments"]
    )
    base = result["base"]
    total = result["total"]

    reply_text = (
        f"💰 *Предварительная стоимость монтажа:*\n"
        f"Базовая оценка: {int(base[0]):,} — {int(base[1]):,} ₽\n"
        f"\n📋 *Корректировки:*\n{breakdown}\n\n"
        f"📦 *Итого:* _{int(total[0]):,} — {int(total[1]):,} ₽_"
    )

    await update.message.reply_text(reply_text, parse_mode="Markdown")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token("7926960422:AAH-OFVzhcdE4gm0KgSuMn9JRxIxSTUrtw0").build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TYPING_EQUIP_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, equipment_cost)],
            ASK_MACHINE_ROOM: [MessageHandler(filters.TEXT, machine_room)],
            ASK_SHAFT_TYPE: [MessageHandler(filters.TEXT, shaft_type)],
            ASK_REPLACEMENT: [MessageHandler(filters.TEXT, replacement)],
            ASK_DOORS: [MessageHandler(filters.TEXT, doors)],
            ASK_PLATFORMS: [MessageHandler(filters.TEXT, platforms)],
            ASK_DISPATCHER: [MessageHandler(filters.TEXT, dispatcher)],
            ASK_REGION: [MessageHandler(filters.TEXT, region)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
