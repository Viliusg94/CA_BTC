import locale

def intcomma(value):
    """
    Formatuoja skaičių su kableliais tūkstantinėms atskirtoms
    
    Pvz.: 1234567 -> 1,234,567
    """
    try:
        locale.setlocale(locale.LC_ALL, '')
        return locale.format_string("%d", value, grouping=True)
    except:
        # Jei locale neveikia, darysim primityviai
        result = ''
        value_str = str(value)
        for i, char in enumerate(reversed(value_str)):
            if i % 3 == 0 and i > 0:
                result = ',' + result
            result = char + result
        return result