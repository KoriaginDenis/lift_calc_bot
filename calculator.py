# calculator.py

def calculate_montage_price(data):
    price_equipment = data.get("equipment_price", 0)

    # === Базовые ставки ===
    base_prices = {
        "пассажирский": 300_000,
        "грузовой": 350_000,
        "малый грузовой": 250_000,
        "больничный": 400_000,
    }
    base = base_prices.get(data.get("lift_type", "").lower(), 300_000)

    # === Надбавки ===
    adjustments = []
    stops = data.get("stops", 0)
    if stops > 1:
        add = stops * 10_000
        adjustments.append(("За количество остановок", add))
        base += add

    if data.get("height", 0) > 20:
        coef = base * 0.05
        adjustments.append(("Высота подъема > 20 м", coef))
        base += coef

    if not data.get("machine_room", True):
        coef = base * 0.10
        adjustments.append(("Без машинного помещения", coef))
        base += coef

    if data.get("fire_mode", False):
        adjustments.append(("РППП (пожарный режим)", 20_000))
        base += 20_000

    if data.get("pass_through", False):
        coef = base * 0.05
        adjustments.append(("Проходная кабина", coef))
        base += coef

    if data.get("doors_more_than_stops", False):
        coef = base * 0.05
        adjustments.append(("Дверей больше, чем остановок", coef))
        base += coef

    # === Регион ===
    region = data.get("region", "СПб")
    if region == "ЛО":
        coef = base * 0.05
        adjustments.append(("Ленинградская область", coef))
        base += coef
    elif region == "регион":
        coef = base * 0.10
        adjustments.append(("Другой регион", coef))
        base += coef

    # === Диспетчеризация ===
    disp = data.get("dispatcher", "").lower()
    if disp == "кристалл":
        adjustments.append(("Диспетчеризация: Кристалл", 40_000))
        base += 40_000
    elif "пк" in disp:
        adjustments.append(("Диспетчеризация: объект с ПК", 20_000))
        base += 20_000

    # === Новостройка ===
    if data.get("is_new_building"):
        if data.get("framing") == "порошковая окраска":
            adjustments.append(("Обрамления: окраска", 15_000))
            base += 15_000
        elif data.get("framing") == "нержавеющая сталь":
            adjustments.append(("Обрамления: нержавейка", 30_000))
            base += 30_000

        if data.get("machine_room", False) and data.get("machine_room_finish", False):
            adjustments.append(("Отделка машинного помещения", 20_000))
            base += 20_000

        if data.get("flooring", False):
            adjustments.append(("Монтаж настилов", 25_000))
            base += 25_000

        if data.get("fencing", False):
            adjustments.append(("Монтаж ограждений", 20_000))
            base += 20_000

    # === Замена ===
    if not data.get("is_new_building"):
        if data.get("caisson", False):
            adjustments.append(("Кессон", 40_000))
            base += 40_000

        if data.get("scrap_by_customer", False):
            coef = base * 0.10
            adjustments.append(("Утилизация заказчиком", coef))
            base += coef

    # === Справочная оценка — 70% от стоимости оборудования
    estimate_by_equipment = price_equipment * 0.7 if price_equipment else None

    return {
        "base_total": base,
        "adjustments": adjustments,
        "estimated_70_percent": estimate_by_equipment
    }
