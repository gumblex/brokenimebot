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

import sys
import time
import json
import queue
import base64
import logging
import hashlib
import requests
import functools
import threading
import concurrent.futures

import jieba
from pypinyin import lazy_pinyin

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

def breakime(text):
    answer = ''
    for word in jieba.cut(text):
        word = word.strip()
        if word:
            pinyin = ' '.join(lazy_pinyin(word))
            answer += ''.join(pinyin[:i+1] for i in range(len(pinyin))) + word
        else:
            answer += ' '
    return answer

def handle_api_update(d: dict):
    logger_botapi.debug('Update: %r' % d)
    try:
        if 'inline_query' in d:
            query = d['inline_query']
            text = query['query'].strip()
            imeresult = breakime(text)
            if imeresult:
                textid = base64.b64encode(hashlib.sha256(imeresult.encode('utf-8')).digest()).decode('ascii')
                r = answer(query['id'], [{'type': 'article', 'id': textid, 'title': imeresult, 'input_message_content': {'message_text': imeresult}}])
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
