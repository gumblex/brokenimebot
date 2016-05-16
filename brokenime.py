#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import jieba
from pypinyin import lazy_pinyin

bopomofo_replace = (
(re.compile('^m(\d)$'), 'mu\\1'),  # 呣
(re.compile('^r5$'), 'er5'),  # 〜兒
(re.compile('iu'), 'iou'),
(re.compile('ui'), 'uei'),
(re.compile('ong'), 'ung'),
(re.compile('^yi?'), 'i'),
(re.compile('^wu?'), 'u'),
(re.compile('iu'), 'v'),
(re.compile('^([jqx])u'), '\\1v'),
(re.compile('([iuv])n'), '\\1en'),
(re.compile('^zhi?'), 'Z'),
(re.compile('^chi?'), 'C'),
(re.compile('^shi?'), 'S'),
(re.compile('^([zcsr])i'), '\\1'),
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
(re.compile('([iv])e'), '\\1E'),
)
bopomofo_table = str.maketrans('bpmfdtnlgkhjqxZCSrzcsiuvaoeEAIOUMNKGR2345', 'ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦˊˇˋ˙')

def breakime(text):
    answer = ''
    for word in jieba.cut(text):
        word = word.strip()
        if word:
            pinyin = ' '.join(lazy_pinyin(word))
            if pinyin == word:
                answer += word
            else:
                answer += ''.join(pinyin[:i+1] for i in range(len(pinyin))) + word
            answer += ''.join(pinyin[:i+1] for i in range(len(pinyin))) + word
        else:
            answer += ' '
    return answer

def bopomofo(pinyin):
    out = pinyin
    for f, r in bopomofo_replace:
        out = f.sub(r, out)
    return out.translate(bopomofo_table)

def breakime(text):
    answers = []
    answer1 = ''
    answer2 = ''
    for word in jieba.cut(text):
        word = word.strip()
        if word:
            pinyinl = lazy_pinyin(word)
            if pinyinl[0] == word:
                answer1 += word
                answer2 += word
            else:
                zhuyin = ' '.join(bopomofo(p) for p in pinyinl)
                pinyin = ' '.join(pinyinl)
                answer1 += ''.join(pinyin[:i+1] for i in range(len(pinyin))) + word
                answer2 += ''.join(zhuyin[:i+1] for i in range(len(zhuyin))) + word
        else:
            answer1 += ' '
            answer2 += ' '
    answers.append((answer1, 'Pinyin'))
    answers.append((answer2, 'Bopomofo'))
    if answer1:
        return answers


if __name__ == '__main__':
    while 1:
        print(breakime(input('> ')))
