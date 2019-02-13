from decimal import Decimal

def calc_pece_grade( has_practexam, pe_grade, ce_grade):
    # PR2016-01-17
    return_pece_grade = 0
    #1. PeCe is 0 als CE niet is ingevuld
    if not ce_grade:
    #. bereken PeCe-cijfer als HasPraktijkexamen (nvt als Examenjaar<2016, wordt bovenin uitgefilterd) '
#PR2016-01-17
        if has_practexam:
    #a. PEcijfer en CEcijfer moeten beide zijn ingevuld
            if not pe_grade:
    #b. bereken gemiddeld PeCe-cijfer
                #  crcPeCe = (crcCEcijfer + crcPEcijfer) / 2 'PR2016-01-16
                #  'c. rond af op 1 cijfer achter de komma
                #   crcPeCe = Int(0.5 + crcPeCe * 10) / 10

                #  crcPeCe_div = (pe_grade + ce_grade) / 2
                crcPeCe_div = Decimal(pe_grade + ce_grade) / Decimal(2)
                #  crcPeCe_mtp = 0.5 + crcPeCe_div * 10
                crcPeCe_mtp =  Decimal(0.5) + Decimal(crcPeCe_div) * 10
                # the floor division operator (//) rounds down to the nearest integer
                #  crcPeCe_mtp = int(crcPeCe_mtp)
                crcPeCe_int = crcPeCe_mtp // 1
    #c. rond af op 1 cijfer achter de komma
                crcPeCe_div = Decimal(crcPeCe_int) / Decimal(10)
                return_pece_grade = crcPeCe_div
        else:
#4. bij geen Praktijkexamen: zet waarde CE in crcPeCe
            return_pece_grade = ce_grade

#5. geef waarde aan ReturnValue
    return return_pece_grade

def round_decimal(x, digits = 0):
    # from https://kfolds.com/rounding-in-python-when-arithmetic-isnt-quite-right-11a79a30390a
    #casting to string then converting to decimal
    x = Decimal(str(x))

    #rounding for integers
    if digits == 0:
        return int(x.quantize(Decimal("1"),  rounding='ROUND_HALF_UP'))

    #string in scientific notation for significant digits: 1e^x
    if digits > 1:
        string =  '1e' + str(-1*digits)
    else:
        string =  '1e' + str(-1*digits)

    #rounding for floating points
    return float(x.quantize(Decimal(string), rounding='ROUND_HALF_UP'))


