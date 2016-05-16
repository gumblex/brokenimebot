#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Broken IME bot - Imitate recently broken Telegram iOS IME support

This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
http://www.wtfpl.net/ for more details.
'''

import re
import sys
import time
import json
import queue
import logging
import requests
import functools
import threading
import concurrent.futures

import jieba
from pypinyin import lazy_pinyin

bopomofo_replace = (
(re.compile('e?r5$'), 'er5'),
(re.compile('([jqx])u'), '$1v'),
(re.compile('yu'), 'v'),
(re.compile('yi?'), 'i'),
(re.compile('wu?'), 'u'),
(re.compile('iu'), 'iou'),
(re.compile('ui'), 'uei'),
(re.compile('ong'), 'ung'),
(re.compile('([iu])n'), '$1en'),
(re.compile('zh'), 'Z'),
(re.compile('ch'), 'C'),
(re.compile('sh'), 'S'),
(re.compile('ai'), 'A'),
(re.compile('ei'), 'I'),
(re.compile('ao'), 'O'),
(re.compile('ou'), 'U'),
(re.compile('ang'), 'K'),
(re.compile('eng'), 'G'),
(re.compile('an'), 'M'),
(re.compile('en'), 'N'),
(re.compile('er'), 'R'),
(re.compile('eh'), 'E'),
(re.compile('([iv])e'), '$1E'),
(re.compile('1'), '')
)
bopomofo_table = str.maketrans('bpmfdtnlgkhjqxZCSrzcsiuvaoeEAIOUMNKGR2345', 'ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦˊˇˋ˙')

logging.basicConfig(stream=sys.stderr, format='%(asctime)s [%(name)s:%(levelname)s] %(message)s', level=logging.DEBUG if sys.argv[-1] == '-v' else logging.INFO)

logger_botapi = logging.getLogger('botapi')

executor = concurrent.futures.ThreadPoolExecutor(5)
HSession = requests.Session()

class AttrDict(dict):

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class BotAPIFailed(Exception):
    pass

def async_func(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        def func_noerr(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception:
                logger_botapi.exception('Async function failed.')
        executor.submit(func_noerr, *args, **kwargs)
    return wrapped

def bot_api(method, **params):
    for att in range(3):
        try:
            req = HSession.get(('https://api.telegram.org/bot%s/' %
                                CFG.apitoken) + method, params=params, timeout=45)
            retjson = req.content
            ret = json.loads(retjson.decode('utf-8'))
            break
        except Exception as ex:
            if att < 1:
                time.sleep((att + 1) * 2)
            else:
                raise ex
    if not ret['ok']:
        raise BotAPIFailed(repr(ret))
    return ret['result']

@async_func
def answer(inline_query_id, results, **kwargs):
    return bot_api('answerInlineQuery', inline_query_id=inline_query_id, results=json.dumps(results), **kwargs)

def updatebotinfo():
    global CFG
    d = bot_api('getMe')
    CFG['username'] = d.get('username')

def getupdates():
    global CFG
    while 1:
        try:
            updates = bot_api('getUpdates', offset=CFG['offset'], timeout=10)
        except Exception:
            logger_botapi.exception('Get updates failed.')
            continue
        if updates:
            #logger_botapi.debug('Messages coming: %r', updates)
            CFG['offset'] = updates[-1]["update_id"] + 1
            for upd in updates:
                MSG_Q.put(upd)
        time.sleep(.2)

def bopomofo(pinyin):
    out = pinyin
    for f, r in bopomofo_replace:
        out = f.sub(r, out)
    return out.translate(bopomofo_table)

def breakime(text):
    answers = []
    answer = ''
    for word in jieba.cut(text):
        word = word.strip()
        if word:
            pinyin = ' '.join(lazy_pinyin(word))
            if pinyin == word:
                answer += word
            else:
                answer += ''.join(pinyin[:i+1] for i in range(len(pinyin))) + word
        else:
            answer += ' '
    answers.append((answer, 'Pinyin'))
    answers.append((bopomofo(answer), 'Bopomofo'))
    return answers

def handle_api_update(d: dict):
    logger_botapi.debug('Update: %r' % d)
    try:
        if 'inline_query' in d:
            query = d['inline_query']
            text = query['query'].strip()
            imeresult = breakime(text)
            if imeresult:
                r = answer(query['id'], [{'type': 'article', 'id': str(time.time()), 'title': ret, 'input_message_content': {'message_text': ret}, 'description': desc} for ret, desc in imeresult])
                logger_botapi.debug(r)
                logger_botapi.info('%s -> %s', text, imeresult)
        elif 'message' in d:
            msg = d['message']
            if msg['chat']['type'] == 'private':
                imeresult = breakime(msg.get('text', '').strip())
                if imeresult:
                    bot_api('sendMessage', chat_id=msg['chat']['id'], text=imeresult, reply_to_message_id=msg['message_id'])
    except Exception:
        logger_botapi.exception('Failed to process a message.')

def load_config():
    return AttrDict(json.load(open('config.json', encoding='utf-8')))

def save_config():
    json.dump(CFG, open('config.json', 'w'), sort_keys=True, indent=1)

if __name__ == '__main__':
    CFG = load_config()
    MSG_Q = queue.Queue()
    jieba.initialize()
    try:
        updatebotinfo()
        apithr = threading.Thread(target=getupdates)
        apithr.daemon = True
        apithr.start()

        while 1:
            handle_api_update(MSG_Q.get())
    finally:
        save_config()
