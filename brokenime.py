#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import jieba
import zhconv
import imelookup

RE_UCJK = re.compile(
    '([\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002A6D6]+)')

enabled_imes = {
    'Pinyin': imelookup.ime_pinyin,
    'Bopomofo': imelookup.ime_zhuyin,
    'Cangjie5': imelookup.ime_cangjie5,
    'Wubi86': imelookup.ime_wubi86,
    'Strokes': imelookup.ime_stroke
}
default_order = [
    ('Pinyin', 'Strokes', 'Wubi86', 'Bopomofo', 'Cangjie5'),
    ('Bopomofo', 'Cangjie5', 'Pinyin', 'Strokes', 'Wubi86')
]

def break_scheme(word, ime):
    code = enabled_imes[ime](word)
    if ime == 'Bopomofo':
        codecat = ''.join(code)
        return ''.join(codecat[:i+1]*3 for i in range(len(codecat))) + word
    elif ime == 'Cangjie5':
        return ''.join(code[0][:i+1] for i in range(len(code[0]))) + word
    else:
        codecat = ' '.join(code)
        return ''.join(codecat[:i+1] for i in range(len(codecat))) + word

def breakime(text):
    text = text.strip()
    if not text:
        return
    answers = dict.fromkeys(enabled_imes, '')
    for word in jieba.cut(text):
        word = word.strip()
        if RE_UCJK.match(word):
            for k in answers:
                answers[k] += break_scheme(word, k)
        else:
            if not word:
                word = ' '
            for k in answers:
                answers[k] += word
    return sorted(answers.items(), key=lambda x: default_order[zhconv.issimp(text, True) is False].index(x[0]))


if __name__ == '__main__':
    while 1:
        print(breakime(input('> ')))
