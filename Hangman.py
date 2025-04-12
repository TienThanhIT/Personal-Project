import random
import time
import os

def clr():
    os.system('cls' if os.name == 'nt' else 'clear')

def chosenword():
    bimat = {#Nhap danh sach cac tu}
    return random.choice(list(bimat))

def timer(s, kt):
    while s>0 and not kt.is_set():
        giay = s % 60
        phut = int(s / 60) % 60
        print(f"Thời gian còn lai: {phut:02}:{giay:02}", end= "\r") 
        time.sleep(1)
        s-=1
    if  s==0:
        kt.set()

def display_hangman(luot):
    trangthai = [ 
                """
                   ------
                   |    |
                   |    O
                   |   /|\\
                   |   / \\
                   |
                """,
                """
                   ------
                   |    |
                   |    O
                   |   /|
                   |   / \\
                   |
                """,
                """
                   ------
                   |    |
                   |    O
                   |    |
                   |   / \\
                   |
                """,
                """
                   ------
                   |    |
                   |    O
                   |    |
                   |   /
                   |
                """,
                """
                   ------
                   |    |
                   |    O
                   |    |
                   |    
                   |
                """,
                """
                   ------
                   |    |
                   |    O
                   |    
                   |   
                   |
                """,
                """
                   ------
                   |    |
                   |    
                   |    
                   |   
                   |
                """,
                """
                   ------
                   |    
                   |    
                   |    
                   |   
                   |
                """
    ]
    return trangthai[luot]

def trangthaigame(hangman, dahoanthien, tusai):
    print(hangman)
    print(dahoanthien)
    print("Các từ đã đoán: " + ", ".join(tusai))

def menu():
    time.sleep(1)
    clr()
    print("CHÀO MỪNG ĐẾN VỚI TRÒ CHƠI HANGMAN")
    print("==================================")
    time.sleep(1)
    print("Hướng dẫn chơi:")
    time.sleep(1)
    print("Trò chơi sẽ chọn một cụm từ bí mật ngẫu nhiên. Mục tiêu của bạn là đoán ra được cụm từ đó.")
    time.sleep(1)
    print("Nếu bạn đoán sai quá 7 lần, bạn sẽ thua!")
    time.sleep(1)
    print("Bạn đã sẵn sàng chơi chưa?")
    time.sleep(1)
    i = input("y: Rồi, bắt đầu chơi!    n: Chưa, thoát khỏi đây\n").strip().lower()
    while i not in ['y', 'n']:
        i = input("Cú pháp nhập không hợp lệ, nhập lại: ").strip().lower()
    if i == 'y':
        play()
    else: 
        exit()

def player_input():
    while True:
        doan = input("Hãy đoán một chữ cái hoặc có thể trả lời đáp án từ bí mật: ").lower().strip()
        return doan

def continuegame():
    i = input("Nhấn 'r' để chơi lại. Nhấn phím bất kì để thoát \n")
    if i == 'r':
        play()
    else: exit()

def play():
    tu = chosenword()
    dahoanthien = "".join(['_' if char != ' ' else ' ' for char in tu]) 
    luot = 7
    tusai = []
    tudadoan = []
    
    while "_" in dahoanthien and luot > 0:
        hangman = display_hangman(luot) 

        clr()
        print(hangman)
        print(dahoanthien)
        print("Các từ đã đoán: "+", ".join(tudadoan))
        doan = player_input()
        clr()

        if len(doan) == 1 and doan.isalpha(): 
            if doan in tudadoan:
                print("Bạn đã đoán chữ này rồi!")
            elif doan not in tu:
                print("Chữ", doan)
                time.sleep(0.5)
                print("Rất tiếc! Không có chữ", doan, "trong từ bí mật")
                luot -= 1
                tusai.append(doan)
                tudadoan.append(doan)
            elif doan in tu:
                count = tu.count(doan)
                print("Chữ ", doan)
                time.sleep(1)
                print(f"Chúc mừng! Có {count} chữ {doan}")
                tubimat = list(dahoanthien)
                hoanthien = [i for i, c in enumerate(tu) if c == doan]
                for index in hoanthien:
                    tubimat[index] = doan
                dahoanthien = ''.join(tubimat)
                tudadoan.append(doan)

        elif len(doan) > 1:
            if doan.strip() == tu:
                time.sleep(2)
                clr()
                dahoanthien = doan  
                print(f"Chúc mừng! '{doan}' là đáp án chính xác!")
            elif doan.isalpha() == False:
                while doan.isalpha() == False:
                    input("Cú pháp nhập không hợp lệ, hãy nhập lại: ")
            else:
                time.sleep(2)
                print("Rất tiếc! Đó không phải là câu trả lời đúng")
                luot -= 1

        if "_" not in dahoanthien:
            print("Bạn đã hoàn thành trò chơi")
            time.sleep(1)
            print(hangman)
            time.sleep(1)
            print("Các từ đã đoán: " + ", ".join(tudadoan))
            time.sleep(1)
            print("======================================")
            continuegame()
            
        elif luot == 0:
            print(display_hangman(0))
            time.sleep(1)
            print("Bạn đã thua...")
            time.sleep(1)
            print("Từ đúng là: ", tu)
            time.sleep(1)
            print("Các từ đã đoán: " + ", ".join(tudadoan))
            time.sleep(1)
            print("======================================")
            continuegame()

if __name__ == "__main__":
    menu()
