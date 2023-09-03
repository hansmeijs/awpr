import re # PR2018-12-31
from random import randint

from awpr import settings as s
from students import models as stud_mod

import logging
logger = logging.getLogger(__name__)


def convert_idnumber_withdots_no_char(id_number):
    # PR2022-06-17
    # function add dots to idnumber, if last 2 digits are not numeric: dont print letters, but print '00' instead

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- convert_idnumber_withdots_no_char -----')

    if logging_on:
        logger.debug('     id_number: ' + str(id_number))
        logger.debug('     len(id_number): ' + str(len(id_number)))
        logger.debug('     id_number[8:]: ' + str(id_number[8:]))

# - delete dots if there are dots in idnumber (should not be possible, but has happened because mod stdent didnt remove dots )
    if id_number and '.' in id_number:
        id_number.replace('.', '')

    sequence_is_numeric = False
    if len(id_number) > 8:
        try:
            sequence_int = int(id_number[8:])
            sequence_is_numeric = True
            if logging_on:
                logger.debug('     sequence_int: ' + str(sequence_int))
                logger.debug('     sequence_is_numeric: ' + str(sequence_is_numeric))
        except:
#  -if last 2 digits are not numeric: dont print letters, print '00' instead
            id_number = id_number[:8] + '00'

    if len(id_number) >= 10:
        id_number_with_dots = '.'.join((id_number[:4], id_number[4:6], id_number[6:8], id_number[8:]))
    elif len(id_number) >= 8:
        id_number_with_dots = '.'.join((id_number[:4], id_number[4:6], id_number[6:]))
    else:
        id_number_with_dots = id_number

    if logging_on:
        logger.debug('     id_number: ' + str(id_number))
        logger.debug('     sequence_is_numeric: ' + str(sequence_is_numeric))

    return id_number_with_dots
# - end of convert_idnumber_withdots_no_char



def get_next_examnumber(sel_school, sel_department):  # PR2021-08-11 PR2023-09-02
    # function gets max exnr of this school and dep and adds 1 to it
    max_exnr = 0

# - loop through students of this school and department
    students = stud_mod.Student.objects.filter(
        school=sel_school,
        department=sel_department
    ).values('examnumber')
    if students:
        for student in students:
            exnr_str = student.get('examnumber')
            if exnr_str:
                # - get first integer part of string
                # from https://stackoverflow.com/questions/11339210/how-to-get-integer-values-from-a-string-in-python
                exnr_int = int(re.search(r'\d+', exnr_str).group())

# - update max_exnr when exnr_int is greater
                if exnr_int and exnr_int > max_exnr:
                    max_exnr = exnr_int
    max_exnr += 1
    # PR2023-09-02 return int, not str
    # was: max_exnr_str = str(max_exnr)
    return max_exnr
# - end of get_next_examnumber



def calc_regnumber_2022(school_code, gender, examyear_str, examnumber_str, depbase_code, levelbase_code, bis_exam):
    # PR2023-08-11 from 2023 regnumber is claculted when printing gradelist ordiploma and stored in DiplomaGradelist
    # function calculates regnumber. This format is used in examyear 2015 and later PR2021-07-19 PR2021-11-17
    #    'structuur registratienummer kandidaat: '12345 6 78910 111213 14 bv: cur02112130021 = cur02-1-1213-002-1
    #    '12345:     SchoolID: CUR01 etc, BON01,
    #    '6:         M=1, V = 2
    #    '78910:     schooljaar
    #    '11,12,13:   volgnr leerling
    #    '14:        1=Havo, 2=Vwo, 3=Tkl, 4=Pkl, 5 = pbl
    logging_on = False  # s.LOGGING_ON

    """
    Het registratienummer bestaat uit 13 tekens en is als volgt opgebouwd:
        1 tm 5: S choolregistratienr:   CUR17
        6:       Geslacht:              M=1, V = 2" & vbCrLf & _
        7 tm 8:  Examenjaar             22 (schooljaar 2021-2022)
        9 tm 12: Examennummer           0001 etc. (001b voor bis examen)
        13:      Studierichting:        1=Havo, 2=Vwo, 3=Tkl, 4=Pkl, 5 = Pbl
    """

    if logging_on:
        logger.debug(' ------- calc_regnumber -------')
        logger.debug('school_code: ' + str(school_code))
        logger.debug('gender:       ' + str(gender))
        logger.debug('examyear_str:     ' + str(examyear_str) + ' ' + str(type(examyear_str)))
        logger.debug('examnumber:   ' + str(examnumber_str) + ' ' + str(type(examnumber_str)))
        logger.debug('depbase_code:      ' + str(depbase_code))
        logger.debug('levelbase_code:    ' + str(levelbase_code))

# - eerste 5 tekens zijn school_code, Fill with '-' if less than 5 characters
    regnr_school_fill = school_code + '-----' if school_code else '-----'
    reg01 = regnr_school_fill[:5]

# - teken 6 is geslacht M=1, V = 2
    reg02 = '-'
    gender_lower = gender.lower() if gender else '-'
    if gender_lower == 'm':
        reg02 = '1'
    elif gender_lower == 'v' or gender_lower == 'f':
        reg02 = '2'

# - teken 7, 8 is examenjaar
    reg03 = examyear_str[2:4] if examyear_str else '--'

# - teken 9, 10, 11 en 12 zijn volgnr kandidaat
    # add 'b' when bis candidate
    if bis_exam:
        examnumber_str += 'b'
    if examnumber_str:
        # PR2022-06-16 get last 4 characters from exam number instead of first 4
        # KAP uses birthdate as exam number, therefore first characters are birth year
        reg04 = ('0000' + examnumber_str)[-4:]
    else:
        reg04 = '----'

# - teken 13: 1 = havo, 2 = vwo, 3 = tkl, 4 = pkl, 5 = pbl
    reg05 = '-'
    if depbase_code:
        depbase_code_lc = depbase_code.lower()
        if depbase_code_lc == 'havo':
            reg05 = '1'
        elif depbase_code_lc == 'vwo':
            reg05 = '2'
        elif depbase_code_lc == 'vsbo':
            if levelbase_code:
                levelbase_code_lc = levelbase_code.lower()
                if levelbase_code_lc == 'tkl':
                    reg05 = '3'
                elif levelbase_code_lc == 'pkl':
                    reg05 = '4'
                elif levelbase_code_lc == 'pbl':
                    reg05 = '5'

    if bis_exam:
        examnumber_str += 'b'
    regnumber = ''.join((reg01, reg02, reg03, reg04, reg05 ))

    if logging_on:
        logger.debug('regnumber: ' + str(regnumber))
    return regnumber
# - end of calc_regnumber



def calc_regnumber(school_code, gender, examyear_str, examnumber_str, depbase_code, levelbase_code, bis_exam, used_regnumber_list):
    # PR2023-08-11 regnumber not in use as of examyear 2023
    # function calculates regnumber. This format is used in examyear 2015 and later PR2021-07-19 PR2021-11-17
    #    'structuur registratienummer kandidaat: '12345 6 78910 111213 14 bv: cur02112130021 = cur02-1-1213-002-1
    #    '12345:     SchoolID: CUR01 etc, BON01,
    #    '6:         M=1, V = 2
    #    '78910:     schooljaar
    #    '11,12,13:   volgnr leerling
    #    '14:        1=Havo, 2=Vwo, 3=Tkl, 4=Pkl, 5 = pbl
    logging_on = False  # s.LOGGING_ON
    """
    was:
    Het registratienummer bestaat uit 13 tekens en is als volgt opgebouwd:
        1 tm 5: Schoolregistratienr:   CUR17
        6:       Geslacht:              M=1, V = 2" & vbCrLf & _
        7 tm 8:  Examenjaar             22 (schooljaar 2021-2022)
        9 tm 12: Examennummer           0001 etc. (001b voor bis examen)
        13:      Studierichting:        1=Havo, 2=Vwo, 3=Tkl, 4=Pkl, 5 = Pbl
    """
    """
    email 31 3 2023
    Ik stel voor het registratienummer op de diploma’s en cijferlijsten als volgt in te richten:

    23c01k999999
    Waarbij:
    •	De eerste twee cijfers zijn het jaartal
    •	De derde letter is ‘c’ voor Curaçao en ‘s’ voor Sint Maarten
    •	Het vierde en vijfde cijfer is het nummer van de schoolcode
    •	Het zesde teken geeft de afdeling en leerweg weer: b voor pbl, k voor pkl, t voor tkl, h voor Havo en v voor vwo
    •	Het getal daarna bestaat uit 6 cijfers en is een uniek nummer dat door AWP wordt gegenereerd.
    De afwisseling tussen cijfers en kleine letters verhoogt de leesbaarheid.

    Het registratienummer  komt in het midden onderaan het waardepapier. Het sedulanummer komt links onder, rechts onder staat het ‘batch’ nummer van het waardepapier.

    Om na te gaan of een diploma of cijferlijst authentiek is kun je het registratienummer opzoeken in AWP. 
    Als het nummer voorkomt in AWP wordt het opgeslagen waardepapier weergegeven. 

    Als het registratienummer van een waardepapier niet voorkomt in AWP of wanneer het niet overeenkomt met de opgeslagen versie, is er sprake van een vervalsing.

    """

    if logging_on:
        logger.debug(' ------- calc_regnumber -------')
        logger.debug('school_code: ' + str(school_code))
        logger.debug('gender:       ' + str(gender))
        logger.debug('examyear_str:     ' + str(examyear_str) + ' ' + str(type(examyear_str)))
        logger.debug('examnumber:   ' + str(examnumber_str) + ' ' + str(type(examnumber_str)))
        logger.debug('depbase_code:      ' + str(depbase_code))
        logger.debug('levelbase_code:    ' + str(levelbase_code))
        logger.debug('used_regnumber_list:    ' + str(used_regnumber_list))

# get regnumber
    # - count is an extra safety to prevent infinite loops, deduct 1 after each loop till 0
    count = 10

    # start of while loop
    exit_loop = False
    regnumber = None
    while not exit_loop:
        count -= 1
        if count < 1:
            exit_loop = True

        if not exit_loop:

            reg_list = []
        # - first 2 characters is examenjaar
            reg_list.append(examyear_str[2:4] if examyear_str else '--')

        # - character 3 id 'c' or 's'
            reg_list.append(school_code[0].lower() if school_code else '-')

        # - character 4 and 5 are 2 digits of schoolcode
            reg_list.append(school_code[3:5].lower() if school_code and len(school_code) > 3 else '--')

        # - character 6: h = havo, v = vwo, t = tkl, k = pkl, b = pbl
            dep_lvl = '-'
            if depbase_code:
                depbase_code_lc = depbase_code.lower()
                if depbase_code_lc == 'havo':
                    dep_lvl = 'h'
                elif depbase_code_lc == 'vwo':
                    dep_lvl = 'v'
                elif depbase_code_lc == 'vsbo':
                    if levelbase_code:
                        levelbase_code_lc = levelbase_code.lower()
                        if levelbase_code_lc == 'tkl':
                            dep_lvl = 't'
                        elif levelbase_code_lc == 'pkl':
                            dep_lvl = 'k'
                        elif levelbase_code_lc == 'pbl':
                            dep_lvl = 'b'
            reg_list.append(dep_lvl)

            reg_list.append(str(randint(1000000, 1999999))[-6:])
            if bis_exam:
                reg_list.append('b')
            try_regnumber = ''.join(reg_list)

            if try_regnumber not in used_regnumber_list:
                regnumber = try_regnumber
    # add new regnumber to used_regnumber_list
                used_regnumber_list.append(regnumber)
                exit_loop = True
    # end of while loop
    if logging_on:
        logger.debug('regnumber: ' + str(regnumber))
    return regnumber
# - end of calc_regnumber


def get_regnumber_info(regnumber):
    info_html = None
    # TODO PR2021-07-23
    """
    /*
        'PR2015-06-13 Regnr hoeft hier niet opnieuw berekend te worden. Laat toch maar staan, maar dan wel opslaan (gebeurt in Property Let Kand_Registratienr
        strNewRegistratienr = pblKand.Kand_Registratienr_Generate(Nz(Me.pge00_txtGeslacht.Value, ""), Nz(Me.pge00_txtExamenNr.Value, ""), Nz(Me.pge00_txtStudierichtingID.Value, 0)) 'PR2014-11-09
        pblKand.Kand_RegistratieNr = strNewRegistratienr
        Me.pge00_txtRegistratieNr.Value = strNewRegistratienr

        strMsgText = "In examenjaar " & CStr(pblAfd.CurSchoolExamenjaar) & " bestaat het registratienummer van een kandidaat" & vbCrLf
        Select Case pblAfd.CurSchoolExamenjaar
        Case Is >= 2015
            strMsgText = strMsgText & "uit 13 tekens en is als volgt opgebouwd:" & vbCrLf & vbCrLf
            If Not strNewRegistratienr = vbNullString Then
                strMsgText = strMsgText & "            " & Left(strNewRegistratienr, 5) & " - " & _
                                 Mid(strNewRegistratienr, 6, 1) & " - " & _
                                 Mid(strNewRegistratienr, 7, 2) & " - " & _
                                 Mid(strNewRegistratienr, 9, 4) & " - " & _
                                 Mid(strNewRegistratienr, 13, 1) & vbCrLf & vbCrLf
            End If
            strMsgText = strMsgText & "1 tm 5:     Schoolregistratienr:   " & pblAfd.CurSchoolRegnr & vbCrLf & _
                                     "6:             Geslacht:                    M=1, V = 2" & vbCrLf & _
                                     "7 tm 8:     Examenjaar                " & Right(CStr(pblAfd.CurSchoolExamenjaar), 2) & " (schooljaar " & pblAfd.CurSchoolSchooljaar & ")" & vbCrLf & _
                                     "9 tm 12:   Examennummer        0001 etc. (001b voor bis examen) " & vbCrLf & _
                                     "13:           Studierichting:          1=Havo, 2=Vwo, 3=Tkl, 4=Pkl, 5 = Pbl."
*/
    """
    return info_html
# - end of get_regnumber_info


def split_prefix(name, is_lastname): # PR2018-12-06
    #PR2016-04-01 aparte functie van gemaakt
    #Functie splitst tussenvoegsel voor Achternaam (IsPrefix=True) of achter Voornamen (IsPrefix=False)
    has_prefix = False
    lastname_or_firstname = ''

    prefix = ''
    prefixes = {
        2: ("d'", "l'"),
        3: ("al", "d'", "da", "de", "do", "el", "l'", "la", "le", "te"),
        4: ("del", "den", "der", "dos", "ten", "ter", "van"),
        6: ("de la", "in 't"),
        7: ("van de", "van 't"),
        8: ("van den", "van der"),
        9: ("voor den", ),
    }
    # sequence van groot naar klein, anders wordt 'van den' niet bereikt, maar ' den ' ingevuld
    sequence = (9, 8, 7, 6, 4, 3, 2)

    name = name.strip()
    if name:
        for x in sequence:
            if len(name) > x:
    # create dict with prefixes with space in front of or behind name
                if x == 2:
                    # don't add spaces to ("d'", "l'"
                    prefixes_with_space = prefixes[x]
                else:

                            # loop through dict works as follows:
                            # for key, value in tpl.items():
                            #     print("{} = {}".format(key, val))
    # loop through tuple:
                    list_with_space = []
                    for value in prefixes[x]:
                        if is_lastname:  # lastname with prefix in front of it: add space after prefix
                            prefix_with_space = value + " "
                        else:  # firstname with prefix behind it: add space before prefix
                            prefix_with_space = " " + value
                        list_with_space.append(prefix_with_space)
                    prefixes_with_space = tuple(list_with_space)

                if is_lastname:  # lastname with prefix in front of it
    # search for prefix at start of name:
                    prefix_search = name[:x]
                    if prefix_search in prefixes_with_space:
                        # get prefix from beginning of name
                        prefix = prefix_search.strip()
                        # get rest_name from end of name
                        lastname_or_firstname = name[x:].strip()
                        has_prefix = True
                else: # firstname with prefix behind it:
    # search for prefix at end of name:
                    prefix_search = name[-x:]
                    if prefix_search in prefixes_with_space:
                        prefix = prefix_search.strip()
                        lastname_or_firstname = name[:-x].strip()
                        has_prefix = True
                if has_prefix:
                    break

        if not has_prefix:
            lastname_or_firstname = name

    return lastname_or_firstname, prefix, has_prefix


def split_fullname(fullname): # PR2018-12-06
    #Function splits fullname into lastname, firstname, prefix
    # in fullname lastame and firstname must be divided by comma "de Groot, Harry" or " Groot, Harry de"

    lastname=''
    firstname = ''
    prefix = ''

    fullname = fullname.strip()
    if fullname:
        # search for comma in name, returns -1 when not found
        index = fullname.find(",")
        if index >= 1: # skip comma at start of string
            has_prefix = False
            lastname = fullname[:index].strip()
            firstname = (fullname[index + 1:].strip())

    # check if there is a prefix in front of lastname
            if lastname:
                lastname_or_firstname, prefix, has_prefix = split_prefix(lastname, True)
                if has_prefix:
                    lastname = lastname_or_firstname

    # check if there is a prefix after firstname
            if not has_prefix and firstname:
                lastname_or_firstname, prefix, has_prefix = split_prefix(firstname, False)
                if has_prefix:
                    firstname = lastname_or_firstname
        else: # if no comma found or coma at position '0'
            lastname = fullname

    return lastname, firstname, prefix


# oooooooooooooo Functions  Student name ooooooooooooooooooooooooooooooooooooooooooooooooooo

def get_firstname_prefix_lastname(last_name, first_name, prefix):  # PR2022-03-05

    _full_name = last_name.strip() if last_name else ''

    _prefix = prefix.strip() if prefix else ''
    if _prefix:
        _full_name = ' '.join((_prefix, _full_name))

    _firstname = first_name.strip() if first_name else ''
    if _firstname:
        _full_name = ' '.join((_firstname, _full_name))

    return _full_name
# - end of get_firstname_prefix_lastname

def get_full_name(last_name, first_name, prefix, has_extrafacilities=False):
    # PR2021-07-26 PR2021-09-05  PR2021-10-07 PR2023-01-07

    _full_name = last_name.strip() if last_name else ''

    _prefix = prefix.strip() if prefix else ''
    if _prefix:
        _full_name = ' '.join((_prefix, _full_name))

    _firstname = first_name.strip() if first_name else ''
    if _firstname:
        _full_name = ', '.join((_full_name, _firstname))

    if has_extrafacilities:
        _full_name += ' *'

    return _full_name
# - end of get_full_name


def get_firstname_initials(first_name):  # PR2021-07-26
    firstname_initials = ''
    first_name = first_name.strip() if first_name else ''
    if first_name:
        # strings '', ' ' and '   ' give empty list [] which is False
        firstnames_arr = first_name.split()
        if firstnames_arr:
            skip = False
            for item in firstnames_arr:
                if not skip:
                    firstname_initials += item + ' '  # write first firstname in full
                    skip = True
                else:
                    if item:
                        # PR2017-02-18 VB debug. bij dubbele spatie in voornaam krijg je lege err(x)
                        firstname_initials += item[:1] + '.'  # write of the next firstnames only the first letter
    return firstname_initials


def get_initials(first_name):  # PR2023-06-13
    initials = ''
    first_name = first_name.strip() if first_name else ''
    if first_name:
        # strings '', ' ' and '   ' give empty list [] which is False
        firstnames_arr = first_name.split()
        if firstnames_arr:
            for item in firstnames_arr:
                if item:
                    initials += item[:1] # dont add dot. was: + '.'
    return initials


def get_lastname_firstname_initials(last_name, first_name, prefix, has_extrafacilities=False):  # PR2021-07-26 PR2023-01-07
    firstname_initials = get_firstname_initials(first_name)
    return get_full_name(last_name, firstname_initials, prefix, has_extrafacilities)


def get_lastname_initials(last_name, first_name, prefix, has_extrafacilities=False):  # PR2023-06-13
    initials = get_initials(first_name)

    last_name = last_name.strip() if last_name else ''
    prefix = prefix.strip() if prefix else ''

    if prefix:
        lastname_initials = ' '.join((prefix, last_name))
    else:
        lastname_initials = last_name

    if initials:
        lastname_initials = ' '.join((lastname_initials, initials))

    if has_extrafacilities:
        lastname_initials += ' *'

    return lastname_initials


# NOT IN USE
def SplitPrefix(name, is_firstname):
    # PR2020-11-15 from AWP PR2016-04-01 aparte functie van gemaakt
    # Functie splits tussenvoegsel voor Achternaam (IsPrefix=True) of achter Voornamen (IsPrefix=False)

    found = False

    remainder = ''
    prefix = ''

    prefixes = ("voor den", "van den", "van der", "van de", "van 't", "de la",
                "del", "den", "der", "dos", "ten", "ter", "van",
                "al", "d'", "da", "de", "do", "el", "l'", "la", "le", "te")

    # search in reverse order of prefix length: check "van den" first,
    # when you check 'van' first, 'van den' will not be reached
    # when booIsPrefix: put space after prefix, but also check "d'" and "l'" without space after prefix
    # when not booIsPrefix: put space before prefix

    prefixes_without_space = ("d'", " l'")

    name_stripped = name.strip()  # 'PR 13 apr 13 Trim toegevoegd
    if name_stripped:
        name_len = len(name_stripped)
        for value in prefixes:
            search_prefix = ' ' + value if is_firstname else value + ' '
            search_len = len(search_prefix)
            if name_len >= search_len:
                if is_firstname:
                    # check for prefix at end of firstname
                    lookup_str = name_stripped[0:search_len]
                else:
                    # check for prefix in front of lastname
                    lookup_str = name_stripped[-name_len]
                if lookup_str == search_prefix:
                    found = True
                    prefix = lookup_str.strip()
                    if is_firstname:
                        remainder = name_stripped[len].strip()
                    else:
                        remainder_len = name_len - search_len
                        remainder = name_stripped[0:remainder_len].strip()
                    break
    # Voornamen met tussenvoegsel erachter
    # van groot naar klein, anders wordt 'van den' niet bereikt, maar 'den' ingevuld

    return found, prefix, remainder  # found returns True when name is split
# End of SplitPrefix

# oooooooooooooo End of Functions Student name ooooooooooooooooooooooooooooooooooooooooooooooooooo