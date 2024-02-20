class Currency:
    decimal_precision = 2
    iso_code = "OVERRIDE"
    symbol = "OVERRIDE"


class CNY(Currency):
    iso_code = "CNY"
    symbol = "¥"
