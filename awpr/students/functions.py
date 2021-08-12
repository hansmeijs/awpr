import re # PR2018-12-31

from awpr import settings as s
from students import models as stud_mod

import logging
logger = logging.getLogger(__name__)


def get_next_examnumber(sel_school, sel_department):  # PR2021-08-11
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
    max_exnr_str = str(max_exnr)
    return max_exnr_str
# - end of get_next_examnumber


def calc_regnumber(regnr_school, gender, examyear_int, examnumber_str, depbase, levelbase):
    # function calculates regnumber. This format is used in examyear 2015 and later PR2021-07-19
    #    'structuur registratienummer kandidaat: '12345 6 78910 111213 14 bv: cur02112130021 = cur02-1-1213-002-1
    #    '12345:     SchoolID: CUR01 etc, BON01,
    #    '6:         M=1, V = 2
    #    '78910:     schooljaar
    #    '11,12,13:   volgnr leerling
    #    '14:        1=Havo, 2=Vwo, 3=Tkl, 4=Pkl, 5 = pbl

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calc_regnumber -------')
        logger.debug('regnr_school: ' + str(regnr_school))
        logger.debug('gender:       ' + str(gender))
        logger.debug('examyear:     ' + str(examyear_int) + ' ' + str(type(examyear_int)))
        logger.debug('examnumber:   ' + str(examnumber_str) + ' ' + str(type(examnumber_str)))
        logger.debug('depbase:      ' + str(depbase))
        logger.debug('levelbase:    ' + str(levelbase))

    # - eerste 5 tekens zijn regnr school
    regnr_school_fill = regnr_school + '-----'
    reg01 = regnr_school_fill[:5]

# - teken 6 is geslacht M=1, V = 2
    reg02 = '-'
    gender_lower = gender.lower() if gender else '-'
    if gender_lower == 'm':
        reg02 = '1'
    elif gender_lower == 'v' or gender_lower == 'f':
        reg02 = '2'

# - teken 7, 8 is examenjaar
    examyear_str = str(examyear_int)
    reg03 = examyear_str[2:4] if examyear_str else '--'

# - teken 9, 10, 11 en 12 zijn volgnr kandidaat
    if examnumber_str:
        examnumber_len = len(examnumber_str)
        if examnumber_len == 4:
            reg04 = examnumber_str
        elif examnumber_len > 4:
            reg04 = examnumber_str[:4]
        else:
            examnumber_fill = '0000' + examnumber_str
            reg04 = examnumber_fill[-4:]
    else:
        reg04 = '----'

# - teken 13: 1 = havo, 2 = vwo, 3 = tkl, 4 = pkl, 5 = pbl
    reg05 = '-'
    if depbase and levelbase:
        depbase_code = depbase.code.lower() if depbase else None
        if depbase_code == 'havo':
            reg05 = '1'
        elif depbase_code == 'vwo':
            reg05 = '2'
        elif depbase_code == 'vsbo':
            levelbase_code = levelbase.code.lower() if levelbase else None
            if levelbase_code == 'tkl':
                reg05 = '3'
            elif levelbase_code == 'pkl':
                reg05 = '4'
            elif levelbase_code == 'pbl':
                reg05 = '5'
    regnumber = ''.join((reg01, reg02, reg03, reg04, reg05 ))

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