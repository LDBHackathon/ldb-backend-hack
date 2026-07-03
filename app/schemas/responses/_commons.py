from typing import Annotated
from decimal import Decimal as DecimalType

from pydantic import PlainSerializer

from app.utils.formatting import decimal_to_float_str

Decimal = Annotated[DecimalType, PlainSerializer(decimal_to_float_str)]
