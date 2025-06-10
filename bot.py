# bot.py

import os
import re
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, Document
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from calculator import calculate_montage_price

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN") or "вставь_свой_токен_сюда"

# Шаги сценария
PDF, REGION, REPLACEMENT, PASS_THROUGH, DOORS_MORE, DISPATCH, EXTRA_QUESTIONS = range(7)

# Временное хранилище данных по пользователю
user_data = {}

# ==== PDF ОБРАБОТКА ====

def parse_pdf_text(text):
    # Упрощённый парсинг
    result = {
        "lift_type": "пассажирский" if "пассажир" in text.lower() else "грузовой",
        "machine_room": "без машинного помещения" not in text.lower(),
        "stops": int(re.search(r"(\d+)\s*останов", text.lower()).group(1)) if re.search(r"(\d+)\s*останов", text.lower()) else 0,
        "height": float(re.search(r"(\d+[.,]?\d*)\s*м", text.lower()).group(1).replace(',', '.')) if re.search(r"(\d+[.,]?\d*)\s*м", text.lower()) else 0,
        "fire_mode": "рппп" in text.lower(),
        "equipment_price": float(re.search(r"([\d\s]+)\s*руб", text.lower()).group(1).replace(' ', '')) if re.search(r"([\d\s]+)\s*руб", text.lower()) else 0
    }
    return result

# ==== СЦЕНАРИЙ ====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте PDF-файл со сметой или ТЗ.")
    return PDF

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file: Document = update.message.document
    if not file.file_name.endswith(".pdf"):
        await update.message.reply_text("Пожалуйста, отправьте именно PDF-файл.")
        return PDF

    file_path = await file.get_file()
    pdf_bytes = await file_path.download_as_bytearray()

    import fitz  # PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(page.get_text() for page in doc)

    parsed = parse_pdf_text(full_text)
    user_data[update.effective_chat.id] = parsed

    await update.message.reply_text(
        "Выберите регион:",
        reply_markup=ReplyKeyboardMarkup(
            [["Санкт-Петербург"], ["Ленинградская область"], ["Другой регион"]],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return REGION

async def set_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    region = update.message.text.lower()
    chat_id = update.effective_chat.id
    user_data[chat_id]["region"] = (
        "СПб" if "петербург" in region else "ЛО" if "ленинград" in region else "регион"
    )

    await update.message.reply_text(
        "Это замена или новостройка?",
        reply_markup=ReplyKeyboardMarkup(
            [["Замена"], ["Новое строительство"]], one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return REPLACEMENT

async def set_replacement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["is_new_building"] = "новое" in update.message.text.lower()

    await update.message.reply_text(
        "Кабина проходная?",
        reply_markup=ReplyKeyboardMarkup([["Да"], ["Нет"]], one_time_keyboard=True, resize_keyboard=True),
    )
    return PASS_THROUGH

async def set_pass_through(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["pass_through"] = update.message.text.lower() == "да"

    await update.message.reply_text(
        "Количество дверей превышает количество остановок?",
        reply_markup=ReplyKeyboardMarkup([["Да"], ["Нет"]], one_time_keyboard=True, resize_keyboard=True),
    )
    return DOORS_MORE

async def set_doors_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["doors_more_than_stops"] = update.message.text.lower() == "да"

    await update.message.reply_text(
        "Тип диспетчеризации?",
        reply_markup=ReplyKeyboardMarkup(
            [["Объект без ПК"], ["Объект с ПК"], ["Кристалл"], ["Без диспетчеризации"]],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return DISPATCH

async def set_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["dispatcher"] = update.message.text

    await update.message.reply_text("Остальные уточнения пока пропущены — расчёт выполняется...")

    return await finalize(update, context)

async def finalize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    data = user_data.get(chat_id, {})

    result = calculate_montage_price(data)

    lines = [f"💰 *Расчёт стоимости монтажа лифта*"]
    lines.append(f"\n*Базовая стоимость:* `{int(result['base_total'])} ₽`")

    if result["adjustments"]:
        lines.append(f"\n*Надбавки:*")
        for name, val in result["adjustments"]:
            lines.append(f"— {name}: `{int(val)} ₽`")

    if result["estimated_70_percent"]:
        lines.append(f"\n📊 *Оценка 70% от оборудования:* `{int(result['estimated_70_percent'])} ₽`")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

# ==== ЗАПУСК ====

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PDF: [MessageHandler(filters.Document.PDF, handle_pdf)],
            REGION: [MessageHandler(filters.TEXT, set_region)],
            REPLACEMENT: [MessageHandler(filters.TEXT, set_replacement)],
            PASS_THROUGH: [MessageHandler(filters.TEXT, set_pass_through)],
            DOORS_MORE: [MessageHandler(filters.TEXT, set_doors_more)],
            DISPATCH: [MessageHandler(filters.TEXT, set_dispatch)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
