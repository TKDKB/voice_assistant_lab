import os
# os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
from datetime import date, datetime
import openai
import tkinter as tk
from tkinter import messagebox
import sqlite3
import speech_recognition
import pyttsx3
import torch

from transformers import GPT2LMHeadModel, GPT2Tokenizer



conn = sqlite3.connect('database.db')
c = conn.cursor()
openai.api_key = "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"
model_engine = "gpt-3.5-turbo-instruct"
max_tokens = 128
# # инициализация инструментов распознавания и ввода речи
recognizer = speech_recognition.Recognizer()
microphone = speech_recognition.Microphone()


def register(username, password):
    c.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()


def login(username, password):
    c.execute("SELECT * FROM Users WHERE username=? AND password=?", (username, password))
    if c.fetchone() is not None:
        return True
    else:
        return False


class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Авторизация")
        self.geometry("300x300")

        self.label_username = tk.Label(self, text="Имя пользователя:")
        self.label_username.pack()

        self.entry_username = tk.Entry(self)
        self.entry_username.pack()

        self.label_password = tk.Label(self, text="Пароль:")
        self.label_password.pack()

        self.entry_password = tk.Entry(self, show="*")
        self.entry_password.pack()

        self.button_register = tk.Button(self, text="Зарегистрироваться", command=self.register_)
        self.button_register.pack()

        self.button_login = tk.Button(self, text="Войти", command=self.login)
        self.button_login.pack()

    def register_(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        c.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
        if not c.fetchone():
            c.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo('Вход выполнен', 'Такой пользователь существует')
        else:
            messagebox.showinfo("Успешно", "Регистрация прошла успешно")
        self.open_menu_window()

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        c.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        if user:
            messagebox.showinfo("Успешно", "Вы успешно вошли в систему")
            self.open_menu_window()
        else:
            messagebox.showerror("Ошибка", "Ошибка авторизации")

    def open_menu_window(self):
        menu_window = tk.Toplevel(self)
        menu_window.title("Главное меню")
        menu_window.geometry("300x300")

        accounts_button = tk.Button(menu_window, text="Начать запись", command=self.open_accounts_window)
        accounts_button.pack()

    def open_accounts_window(self):
        # self.withdraw()
        another_window = AccountsWindow()
        another_window.assistant()
        another_window.withdraw()


class AccountsWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()

    @staticmethod
    def say(reply: str):
        engine = pyttsx3.init()
        engine.say(reply)
        engine.runAndWait()

    @staticmethod
    def record_and_recognize_audio(*args: tuple):
        """
        Запись и распознавание аудио
        """
        with microphone:
            recognized_data = ""

            # регулирование уровня окружающего шума
            recognizer.adjust_for_ambient_noise(microphone, duration=2)

            try:
                print("Listening...")
                audio = recognizer.listen(microphone, 5, 5)

            except speech_recognition.WaitTimeoutError:
                print("Can you check if your microphone is on, please?")
                return

            # использование online-распознавания через Google
            try:
                print("Started recognition...")
                recognized_data = recognizer.recognize_google(audio, language="ru").lower()

            except speech_recognition.UnknownValueError:
                pass

            # в случае проблем с доступом в Интернет происходит выброс ошибки
            except speech_recognition.RequestError:
                print("Check your Internet Connection, please")

            return recognized_data

    @classmethod
    def assistant(cls):
        time_prompt = ["сколько время", "сколько времени", "время"]
        date_prompt = ["какое сегодня число", "дата"]
        voice_input = cls.record_and_recognize_audio()
        cls.say(voice_input)
        print(voice_input)
        if voice_input in date_prompt:
            current_date = date.today()
            result = str(current_date.day) + " " + str(current_date.month) + " " + str(current_date.year)
            cls.say(result)
        elif voice_input in time_prompt:
            current_time = datetime.now().time()
            result = str(current_time).split(":")[0] + " " + str(current_time).split(":")[1]
            cls.say(result)
        elif voice_input == "стоп":  # окончание работы по команде "стоп"
            cls.say("до свидания")
            quit()
        else:
            reply = cls.gpt(voice_input)
            cls.say(reply)

    @staticmethod
    def gpt(prompt):
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=1024,
            temperature=0.5,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        reply = completion.choices[0].text
        # return reply
        # input_ids = tokenizer.encode(prompt, return_tensors="pt").cuda()
        # out = model.generate(input_ids.cuda())
        # generated_text = list(map(tokenizer.decode, out))[0]
        # return generated_text
        #     if openai.api_key == "":
        #         cls.say("У вас нет ключа")
        #     else:
        # message = prompt
        #
        # #messages.append({"role": "user", "content": message})
        # chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=message)
        # reply = chat.choices[0].message.conten
        return reply


if __name__ == "__main__":
    app = Application()
    app.mainloop()
