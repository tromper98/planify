import enum

class AppointmentStatusEnum(enum.Enum):
    PENDING = "pending" # встреча забронирована, ожидает подтверждения
    CONFIRMED = "confirmed" # встреча подтверждена
    COMPLETED = "completed" # встреча завершена
    CANCELLED = "cancelled" # встреча отменена