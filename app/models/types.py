import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class SignalStatus(str, enum.Enum):
    PENDING = "PENDING"  # Waiting for entry price
    ACTIVE = "ACTIVE"  # Entry triggered, trade is live
    HIT_TARGET = "HIT_TARGET"  # Profit booked
    HIT_STOP_LOSS = "HIT_STOP_LOSS"  # Stop loss hit
    EXPIRED = "EXPIRED"  # Time horizon expired before entry
    MANUAL_CLOSE = "MANUAL_CLOSE"  # Admin manually closed the trade


class UserTradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class SetupType(str, enum.Enum):
    BREAKOUT = "BREAKOUT"
    PULLBACK = "PULLBACK"
    REVERSAL = "REVERSAL"
    MOMENTUM = "MOMENTUM"
    VALUE = "VALUE"
    NEUTRAL = "NEUTRAL"


class SignalAction(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class NotificationType(str, enum.Enum):
    NEW_SIGNAL = "NEW_SIGNAL"
    SIGNAL_UPDATE = "SIGNAL_UPDATE"  # e.g. Target Hit
    RISK_ALERT = "RISK_ALERT"  # e.g. Stop Loss approaching
    SYSTEM = "SYSTEM"  # Maintenance, etc.


class PlatformType(str, enum.Enum):
    IOS = "IOS"
    ANDROID = "ANDROID"
    WEB = "WEB"
