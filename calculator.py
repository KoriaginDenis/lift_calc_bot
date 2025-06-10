# calculator.py

def calculate_montage_price(equipment_price, params):
    base_min = equipment_price * 0.60
    base_max = equipment_price * 0.70
    adjustments = []

    # Коэффициенты
    if params["no_machine_room"]:
        adjustments.append(("Нет машинного помещения", 0.05))
    if params["shaft_type"] == "металлическая":
        adjustments.append(("Тип шахты: металлическая", 0.05))
    elif params["shaft_type"] == "кирпичная":
        adjustments.append(("Тип шахты: кирпичная", 0.10))
    if params["replacement"]:
        adjustments.append(("Замена лифта", 0.10))
    if params["more_doors"]:
        adjustments.append(("Проходная кабина", 0.05))
    if params["we_do_platforms"]:
        adjustments.append(("Настилы делаем мы", 0.03))
    if params["dispatcher"] == "IP":
        adjustments.append(("Диспетчерская IP", 0.04))
    if params["region"]:
        adjustments.append(("Объект в регионе", 0.07))

    total_min = base_min
    total_max = base_max

    breakdown = []
    for label, coef in adjustments:
        delta_min = base_min * coef
        delta_max = base_max * coef
        total_min += delta_min
        total_max += delta_max
        breakdown.append((label, delta_min, delta_max))

    return {
        "base": (base_min, base_max),
        "adjustments": breakdown,
        "total": (total_min, total_max)
    }
