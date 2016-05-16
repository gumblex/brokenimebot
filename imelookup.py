#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import collections
from threading import RLock

import zhconv
from pypinyin import lazy_pinyin

PATH = 'data'

_fill_lock = RLock()

class LazyDict(collections.UserDict):
    """Dictionary populated on first use."""
    data = None
    def __getitem__(self, key):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return self.data[key]

    def get(self, key, default=None):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return self.data.get(key, default)

    def __contains__(self, key):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return key in self.data

    def __iter__(self):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return iter(self.data)

    def __len__(self):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return len(self.data)

    def keys(self):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return self.data.keys()

class ReverseLookupTable(LazyDict):
    """Map characters to corresponding code using Rime dictionary files.
    """
    def _fill(self):
        data = {}
        started = False
        with open(self.dictfile, 'r', encoding='utf-8') as f:
            for ln in f:
                ln = ln.strip()
                if started and ln and ln[0] != '#':
                    l = ln.split('\t')
                    # we assume one-to-one correspondence
                    data[l[0]] = l[1]
                elif ln == '...':
                    started = True
        self.data = data

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
bopomofo_table = str.maketrans('bpmfdtnlgkhjqxZCSrzcsiuvaoeEAIOUMNKGR2345',
    'ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦˊˇˋ˙')

def translate_bopomofo(pinyin):
    out = pinyin
    for f, r in bopomofo_replace:
        out = f.sub(r, out)
    return out.translate(bopomofo_table)

def fn_map_code(dic, trans={}):
    return lambda s: [dic.get(c, c).translate(trans) for c in s]

ime_pinyin = lazy_pinyin
ime_zhuyin = lambda s: list(map(translate_bopomofo, lazy_pinyin(s)))

table_cangjie5 = ReverseLookupTable()
table_cangjie5.dictfile = os.path.join(PATH, 'cangjie5.dict.yaml')
ime_cangjie5 = fn_map_code(table_cangjie5, str.maketrans(
    'abcdefghijklmnopqrstuvwxyz~',
    '日月金木水火土竹戈十大中一弓人心手口尸廿山女田難卜符～'))
table_wubi86 = ReverseLookupTable()
table_wubi86.dictfile = os.path.join(PATH, 'wubi86.dict.yaml')
ime_wubi86 = fn_map_code(table_wubi86)
table_stroke = ReverseLookupTable()
table_stroke.dictfile = os.path.join(PATH, 'stroke.dict.yaml')
ime_stroke = fn_map_code(table_stroke, str.maketrans('hspnz', '一丨丿丶乙'))
