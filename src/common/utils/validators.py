from datetime import datetime

def validate_date(date_str: str) -> bool:
    """Валидация даты"""
    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        return date_obj >= datetime.now().date()
    except ValueError:
        return False

def validate_time(time_str: str) -> bool:
    """Валидация времени"""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def validate_duration(minutes: int) -> bool:
    """Валидация продолжительности"""
    return 15 <= minutes <= 480  # От 15 минут до 8 часов