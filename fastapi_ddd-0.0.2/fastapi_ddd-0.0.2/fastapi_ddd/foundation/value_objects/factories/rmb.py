from decimal import Decimal
from typing import Union

from fastapi_ddd.foundation.value_objects import Money, currency


def get_rmb(amount: Union[Decimal, int, float, str]) -> Money:
    return Money(currency.CNY, amount)


def get_rmb_from_cent(amount_cent: Union[Decimal, int, float, str]) -> Money:
    return Money(currency.CNY, '%.2f' % (amount_cent / 100.0))
