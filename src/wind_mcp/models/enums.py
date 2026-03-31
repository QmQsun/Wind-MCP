from enum import Enum


class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class Periodicity(str, Enum):
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"
    QUARTERLY = "Q"
    SEMI_ANNUAL = "S"
    YEARLY = "Y"


class BarInterval(str, Enum):
    MIN_1 = "1"
    MIN_3 = "3"
    MIN_5 = "5"
    MIN_10 = "10"
    MIN_15 = "15"
    MIN_30 = "30"
    MIN_60 = "60"


class DayType(str, Enum):
    TRADING = "Trading"
    WEEKDAYS = "Weekdays"
    ALL_DAYS = "Alldays"


class TradingCalendar(str, Enum):
    SSE = "SSE"          # Shanghai Stock Exchange (default)
    SZSE = "SZSE"        # Shenzhen
    HKEX = "HKEX"        # Hong Kong
    NYSE = "NYSE"        # New York
    NASDAQ = "NASDAQ"
    LSE = "LSE"          # London
    TSE = "TSE"          # Tokyo
