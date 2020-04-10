import os
from pathlib import Path
import json
import config
import requests
import telebot
from random import randint
import time

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


def data_load(json_file):
    data = json.load(open(json_file))
    return data


qData = data_load('quiz.json')
uData = data_load('users.json')


def user(user_id, questions_list, count):
    data = {
        'id': user_id,
        'questions': questions_list,
        'true_answers': count
    }
    return data


def json_users_file_update(user, json_file='users.json'):
    try:
        users = json.load(open(json_file))
    except:
        users = []
        users.append(user)
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def json_quiz_file(text_path, json_file='quiz.json'):
    File = data_question(questions_list(get_text(text_path)))
    try:
        data = json.load(open(json_file))
    except:
        data = []
    data += File
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(File, f, indent=2, ensure_ascii=False)


def user_checker(user_id):
    count = 0
    for i in uData:
        if uData[i]['id'] == user_id:
            count = uData[i]['true_answers']
            questions = uData[i]['questions']
            uData.pop(i)
            current_players.update({user_id: ['', count]})
            return questions

    questions = [i for i in range(len(qData))]
    current_players.update({user_id: ['', count]})
    return questions


def pull_of_questions(questions):
    pull = []
    for i in range(10):
        pull.append(questions.pop(randint(0, len(questions))))
    return pull


def generate_markup(answers):
    markup = telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True)
    for item in answers:
        markup.add(item)
    return markup


current_players = {}


def current_answer(id):
    bullshit = qData[id]['answers'][int(qData[id]['right_answer'])-1]
    return bullshit


def question_generation(question, answers, user_id, pull, user_questions, current_question_id):
    current_players.update(
    {user_id: [current_answer(current_question_id), current_players[user_id][1], pull, user_questions]})
    markup = generate_markup(answers)
    bot.send_message(user_id, question, reply_markup=markup)

def game(user_id):
    i = current_players[user_id][2].pop()
    question_generation(qData[i]['text_name'], qData[i]['answers'], user_id, current_players[user_id][2],current_players[user_id][3], i)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет!')


@bot.message_handler(commands=['quizPls'])
def quiz(message):
    user_id = message.from_user.id
    user_questions = user_checker(user_id)
    if len(user_questions) > 10:
        pull = pull_of_questions(user_questions)
    else:
        pull, user_questions = user_questions, []
    current_players.update(
         {user_id: ["", current_players[user_id][1], pull, user_questions]})
    game(user_id)



@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_answer(message):
    user_id = message.from_user.id
    keyboard_hider = telebot.types.ReplyKeyboardRemove()
    answer = current_players[user_id][0]
    text = message.text
    if text == answer:
        current_players[user_id][1] += 1
        bot.send_message(message.chat.id, 'Верно!',
                         reply_markup=keyboard_hider)
    else:
        bot.send_message(
            message.chat.id, 'Правильный ответ: {}'.format(answer),
            reply_markup=keyboard_hider)
    if current_players[user_id][2]!=[]:
        game(user_id)
    else:
        json_users_file_update(user(user_id, current_players[user_id][3],
                    current_players[user_id][1]))


bot.polling()
