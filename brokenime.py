#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import jieba
from pypinyin import lazy_pinyin

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

if __name__ == '__main__':
    while 1:
        print(breakime(input('> ')))
