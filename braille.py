
def text_to_braille(text):
    # Braille Unicode mappings
    braille_map = {
        'a': '\u2801', 'b': '\u2803', 'c': '\u2809', 'd': '\u2819',
        'e': '\u2811', 'f': '\u280b', 'g': '\u281b', 'h': '\u2813',
        'i': '\u280a', 'j': '\u281a', 'k': '\u2805', 'l': '\u2807',
        'm': '\u280d', 'n': '\u281d', 'o': '\u2815', 'p': '\u280f',
        'q': '\u281f', 'r': '\u2817', 's': '\u280e', 't': '\u281e',
        'u': '\u2825', 'v': '\u2827', 'w': '\u283a', 'x': '\u282d',
        'y': '\u283d', 'z': '\u2835', ' ': ' ', '#': '\u283c'  # braille number sign 
    }


    number_to_braille = {
    '1': braille_map['a'], '2': braille_map['b'], '3': braille_map['c'],
    '4': braille_map['d'], '5': braille_map['e'], '6': braille_map['f'],
    '7': braille_map['g'], '8': braille_map['h'], '9': braille_map['i'],
    '0': braille_map['j']
    }

    braille_text = []
    is_number_mode = False
    for char in text.lower():

        if char.isdigit():
            if not is_number_mode:

                braille_text.append(braille_map['#']) #needs to start with hastag to tell user to numbers are being expressed
                is_number_mode = True 
            braille_text.append(number_to_braille[char]) # find the number equivalent in braille

        elif char.isalpha():

            if is_number_mode: #outputs the braille hashtag to tell user that words are being expressed now

                braille_text.append(braille_map['#'])
                is_number_mode = False

            braille_text.append(braille_map[char]) #finds equivalent for letter

        else:
            braille_text.append(braille_map.get(char, '?'))
          

    # join the list into a single string
    braille_text = ''.join(braille_text)


    # now the braille will be turned into physical braille based on servo output and input

    return braille_text

word = "123 sesame street"
braille_equiv = print(text_to_braille(word))

  





    
    