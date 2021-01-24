from decimal import Decimal


def round_decimal(x, digits=0):
    # from https://realpython.com/python-rounding/

    # casting to string then converting to decimal
    x = Decimal(str(x))

    # rounding for integers
    decimal_string = None
    if digits == 0:
        decimal_string = "1"
    elif digits == 1:
        decimal_string ="1.0"
    elif digits == 2:
        decimal_string ="1.00"

    #rounding for floating points
    return x.quantize(Decimal(decimal_string),  rounding='ROUND_HALF_UP')


