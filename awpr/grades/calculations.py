from decimal import Decimal


def round_decimal_from_str(input_str, digits=0):  # PR2021-12-13
    # from https://realpython.com/python-rounding/
    # >>> Decimal("1.65").quantize(Decimal("1.0"))
    # The Decimal("1.0") argument in .quantize() determines the number of decimal places to round the number.

    #  input_str must use dot, no comma, otherwise gets error decimal.InvalidOperation: <class 'decimal.ConversionSyntax'>

    # The decimal.ROUND_HALF_UP method rounds everything to the nearest number and breaks ties by rounding away from zero:
    # >>> decimal.getcontext().rounding = decimal.ROUND_HALF_UP

    # casting to string then converting to decimal
    input_decimal = Decimal(str(input_str))

    # rounding for floating points
    output_decimal = round_decimal(input_decimal, digits)
    return output_decimal


def round_decimal(input_decimal, digits=0):
    # from https://realpython.com/python-rounding/
    # >>> Decimal("1.65").quantize(Decimal("1.0"))
    # The Decimal("1.0") argument in .quantize() determines the number of decimal places to round the number.

    #  input_str must use dot, no comma, otherwise gets error decimal.InvalidOperation: <class 'decimal.ConversionSyntax'>

    # The decimal.ROUND_HALF_UP method rounds everything to the nearest number and breaks ties by rounding away from zero:
    # >>> decimal.getcontext().rounding = decimal.ROUND_HALF_UP

    # - set number of digits after the dot
    decimal_string = None
    if digits == 0:
        decimal_string = "1"
    elif digits == 1:
        decimal_string ="1.0"
    elif digits == 2:
        decimal_string ="1.00"

    #rounding for floating points
    output_decimal = input_decimal.quantize(Decimal(decimal_string), rounding='ROUND_HALF_UP')
    return output_decimal

