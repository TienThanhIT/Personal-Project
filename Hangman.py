#LAB1
#======================================================
def swap_first_characters(str1, str2):
    if len(str1) < 2 or len(str2) < 2:
        return "Cả hai chuỗi phải có ít nhất 2 ký tự."
    
    new_str1 = str2[:2] + str1[2:] 
    new_str2 = str1[:2] + str2[2:] 
    
    return f"{new_str1} {new_str2}"

result = swap_first_characters('gps', 'fpt')
print(result)

#========================================================

def remove_even_index_chars(s):
    return ''.join([s[i] for i in range(len(s)) if i % 2 != 0])

result = remove_even_index_chars('Dai hoc Can Tho')
print(result) 

#========================================================

def count_word(sentence):

    words = sentence.split()
    
    word_count = {}
    
    for word in words:
    
        word = word.lower()
        if word in word_count:
            word_count[word] += 1
        else:
            word_count[word] = 1
            
    return word_count


result = count_word('Co cong mai sat, co ngay nen kim')
print(result)  

#======================================================

def mahoa(s):
    encoded = ''
    for char in s:
        if char.isalpha():
            new_char = chr((ord(char) - ord('a') - 3) % 26 + ord('a')) if char.islower() else chr((ord(char) - ord('A') - 3) % 26 + ord('A'))
            encoded += new_char
        else:
            encoded += char  
    return encoded

result = mahoa('Tinhoclythuyet')
print(result) 

#=====================================================

def is_valid_string(s, allowed_chars):
    allowed_set = set(allowed_chars)
    for char in s:
        if char not in allowed_set:
            return False  
    
    return True  

allowed_characters = '012'  
print(is_valid_string('0011', allowed_characters))  
print(is_valid_string('12', allowed_characters))    
print(is_valid_string('012', allowed_characters))
print(is_valid_string('122', allowed_characters))   
print(is_valid_string('123', allowed_characters))   
print(is_valid_string('24', allowed_characters)) 

#==================================================

def string_to_list(s):
    return s.split()

result = string_to_list('Cau dua du xoai')
print(result)

#==================================================

def khongtrung(s):
    s = s.lower()
  
    char_count = {}

    for char in s:
        char_count[char] = char_count.get(char, 0) + 1

    for char in s:
        if char_count[char] == 1:
            return char
    
    return None


print(khongtrung('abcdef'))     
print(khongtrung('abcabcdef'))   
print(khongtrung('aabbcc'))      
print(khongtrung('AaBbCc'))       
print(khongtrung('aA'))  

#===================================================

def bokhoangtrang(s):
    return s.replace(' ', '')


result = bokhoangtrang('Dai hoc Can Tho')
print(result)  

#===================================================

def laptu(s):
    s = s.lower()
    words = s.split()
  
    seen = set()
    

    for word in words:
        if word in seen:
            return word
        seen.add(word)
    return None 


result = laptu('Co cong mai sat, co ngay nen kim')
print(result)
  
#====================================================

def day0dainhat(s):
    max_length = 0  
    current_length = 0  

    for char in s:
        if char == '0':
            current_length += 1  
        else:
            max_length = max(max_length, current_length)  
            current_length = 0  
  
    max_length = max(max_length, current_length)

    return max_length


result = day0dainhat('0000000100100011')
print(result)

#==================================================

