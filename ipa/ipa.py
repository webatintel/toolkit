# -*- coding:utf-8 -*-

# pip install eng_to_ipa

import tkinter as tk
import tkinter.messagebox

import eng_to_ipa
import random


def get_random_word():
    random_index = random.randint(0, len(words))
    return words[random_index]

def get_ipa():
    return ', '.join(eng_to_ipa.ipa_list(random_word)[0])

def check_answer():
    if word.get() == random_word:
        tk.messagebox.showinfo(title="结果", message="正确")
    else:
        tk.messagebox.showinfo(title="结果", message="错误")


def show_answer():
    tk.messagebox.showinfo(title="正确答案", message=random_word)


def next():
    global random_word
    random_word = get_random_word()
    print(random_word)
    ipa["text"] = get_ipa()
    word.delete(0, tk.END)


f = open("word.txt")
words = f.read().split()
f.close()

FONT_FAMILY = "Arial"
FONT_SIZE1 = 50
FONT1 = (FONT_FAMILY, FONT_SIZE1)

FONT_SIZE2 = 30
FONT2 = (FONT_FAMILY, FONT_SIZE1)

window = tk.Tk()
window.title("国际音标学习")
width = window.winfo_screenwidth()
height = window.winfo_screenheight()
window.geometry("%dx%d" % (width, height))

random_word = get_random_word()

ipa = tk.Label(window, text=get_ipa(), font=FONT1)
ipa.pack()

word = tk.Entry(window, show=None, font=FONT1)
word.pack()
word.focus()

tk.Button(window, text="检查答案(C)", command=check_answer, font=FONT2).pack()
window.bind('<Control-c>',lambda event:check_answer())

tk.Button(window, text="显示答案(s)", command=show_answer, font=FONT2).pack()
window.bind('<Control-s>',lambda event:show_answer())

tk.Button(window, text="下一个(n)", command=next, font=FONT2).pack()
window.bind('<Control-n>',lambda event:next())

window.mainloop()
