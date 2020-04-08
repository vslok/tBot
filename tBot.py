import os
from pathlib import Path
import json
import config
import requests
import telebot
import random

bot = telebot.TeleBot(config.token)


def get_text(url, encoding='utf-8', to_lower=False):
    url = str(url)
    if url.startswith('http'):
        r = requests.get(url)
        if not r.ok:
            r.raise_for_status()
        return r.text.lower() if to_lower else r.text
    elif os.path.exists(url):
        with open(url, encoding=encoding, errors='ignore') as f:
            return f.read().lower() if to_lower else f.read()
    else:
        raise Exception('parameter [url] can be either URL or a filename')


def questions_list(f):
    f = f.split(';')
    f.pop()
    return f


def data_question(qlist):
    data = []
    for i in range(0, len(qlist), 6):
        question = {
			'id': len(data),
            'text_name': qlist[i].replace('\n', '', 1),
            'answers': [qlist[j].replace('\n', '') for j in range(i+1, i+5)],
            'right_answer': qlist[i+5].replace('\n', ''),
            'true': 0,
            'false': 0
        }
        data.append(question)
    return data

# def json_users_file(json_file='users.json'):


def json_quiz_file(text_path, json_file='quiz.json'):
    File = data_question(questions_list(get_text(text_path)))
    try:
        data = json.load(open(json_file))
    except:
        data = []
    data.append(File)
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(File, f, indent=2, ensure_ascii=False)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет!/n')
