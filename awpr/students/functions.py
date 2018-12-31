import re # PR2018-12-31
import logging
logger = logging.getLogger(__name__)



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