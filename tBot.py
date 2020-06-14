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
    try:
        data = json.load(open(json_file))
    except:
        data = []
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

# def json_stat_file_update(json_file ='stat.json'):
#     with open(json_file, 'w', encoding='utf-8') as f:
#         json.dump

def json_users_file_update(user, json_file='users.json'):
    uData.append(user)
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(uData, f, indent=2, ensure_ascii=False)

def questions_file_update(json_file='quiz.json'):
    for key in questons_session_stat.keys():
        if questons_session_stat[key] == True:
            qData[key]["true"] +=1
        else:
            qData[key]["false"] +=1
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(qData, f, indent=2, ensure_ascii=False)


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
    for i in range(len(uData)):
        if uData[i]['id'] == user_id:
            count = uData[i]['true_answers']
            questions = uData[i]['questions']
            uData.pop(i)
            current_players.update({user_id: ['', count]})
            return questions
    questions = [i for i in range(len(qData))]
    current_players.update({user_id: ['', 0]})
    return questions


def pull_of_questions(questions):
    pull = []
    for i in range(10):
        pull.append(questions.pop(randint(0, len(questions)-1)))
    return pull


def generate_markup(answers):
    markup = telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True)
    for item in range(len(answers)):
        markup.add(str(item+1))
    return markup


current_players = {}


def current_answer(id):
    bullshit = qData[id]['right_answer']
    return bullshit

questons_session_stat = {}

def question_gen(question, answers):
    mes = question+'\n'
    for i in range(len(answers)):
        mes+= '\n {}. '.format(i+1) + answers[i]
    return mes

def question_generation(question, answers, user_id, pull, user_questions, current_question_id):
    current_players.update(
    {user_id: [current_answer(current_question_id), current_players[user_id][1], pull, user_questions, current_players[user_id][4],current_question_id]})
    markup = generate_markup(answers)
    bot.send_message(user_id, question_gen(question, answers), reply_markup=markup)

def game(user_id):
    i = current_players[user_id][2].pop()
    question_generation(qData[i]['text_name'], qData[i]['answers'], user_id, current_players[user_id][2],current_players[user_id][3], i)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет!')


Flag = False
@bot.message_handler(commands=['quizPls'])
def quiz(message):
    global Flag
    Flag = True
    sTime = time.monotonic()
    user_id = message.from_user.id
    user_questions = user_checker(user_id)
    if len(user_questions) > 10:
        pull = pull_of_questions(user_questions)
    else:
        pull, user_questions = user_questions, [i for i in range(len(qData))]
    current_players.update(
        {user_id: ["", current_players[user_id][1], pull, user_questions, sTime, 0]})
    game(user_id)



@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_answer(message):
    global Flag
    if Flag:
        user_id = message.from_user.id
        keyboard_hider = telebot.types.ReplyKeyboardRemove()
        answer = current_players[user_id][0]
        text = message.text
        if text == answer:
            current_players[user_id][1] += 1
            bot.send_message(message.chat.id, 'Верно!',
                            reply_markup=keyboard_hider)
            questons_session_stat[current_players[user_id][5]] = True
        else:
            bot.send_message(
                message.chat.id, 'Правильный ответ: {}'.format(answer),
                reply_markup=keyboard_hider)
            questons_session_stat[current_players[user_id][5]] = False
        if current_players[user_id][2]!=[] and (time.monotonic()-current_players[user_id][4])<720.0:
            game(user_id)
        elif (time.monotonic()-current_players[user_id][4])>720.0:
            bot.send_message(
                message.chat.id, 'Всего правильных ответов: {}'.format(current_players[user_id][1])
                    +'\n'+'Вышло время сессии')
            json_users_file_update(user(user_id, current_players[user_id][3],
                        current_players[user_id][1]))
            questions_file_update()
            Flag = False
        else:
            bot.send_message(
                message.chat.id, 'Всего правильных ответов: {}'.format(current_players[user_id][1]))
            json_users_file_update(user(user_id, current_players[user_id][3],
                        current_players[user_id][1]))
            questions_file_update()
            Flag = False


bot.polling()
