from nltk.corpus import wordnet
from flask_bootstrap import Bootstrap
from flask import Flask, redirect, render_template, request
from os.path import dirname, join

import itertools as itr

import random
import string
import json

CONFIG_PATH = join(dirname(__file__), "config.json")

CONFIG = json.load(open(CONFIG_PATH))

app = Flask(__name__)


def save_config(
):
    json.dump(CONFIG, open(CONFIG_PATH, "w"))


def add_ixnclude(
    #
    synA,
    synB,
    is_inc,
):
    type_ = "include" if is_inc else "exclude"
    synA = synA.lower().strip()
    synB = synB.lower().strip()

    if CONFIG[type_].get(synA) == None:
        CONFIG[type_][synA] = []

    if CONFIG[type_].get(synB) == None:
        CONFIG[type_][synB] = []

    if synB not in CONFIG[type_][synA]:
        CONFIG[type_][synA].append(synB)
    if synA not in CONFIG[type_][synB]:
        CONFIG[type_][synB].append(synA)

    save_config()


def g_length(
    #
        word):
    return sum([CONFIG["sizes"][i] for i in word])


def g_syns(
    #
        word):
    word = word.lower()
    syns = list(set(
        [y.replace('_', ' ') for x in wordnet.synsets(word)
         for y in x.lemma_names() if y != word]
    ))
    syns = syns + CONFIG["include"].get(word, [])
    return [x for x in syns if x not in CONFIG["exclude"].get(word, [])]


def g_syns_map(
        syns,
        word):
    return {x: g_length(x)-g_length(word) for x in syns if g_length(x) - g_length(word) != 0}


def g_replc(
    #
        length,
        syns_dicts):
    result = []
    syns_dicts = {
        k: [(k, k1, v1) for k1, v1 in v.items()] for k, v in syns_dicts.items()
    }

    for i in range(1, len(syns_dicts)+1):
        for c in itr.combinations(syns_dicts, i):
            prods = itr.product(
                * [syns_dicts[c_] for c_ in c]
            )
            for prod in prods:
                if sum([x[2] for x in prod]) == length:
                    result.append(prod)
    return result


def g_suggs(
    #
        text,
        length,
        can_rep):
    can_rep = can_rep.split(',')
    length = length - g_length(text)
    syns = {x: g_syns_map(g_syns(x), x) for x in can_rep}
    replcs = g_replc(length, syns)

    result = []
    for repl in replcs:
        text_ = text
        for org, rep, ln in repl:
            text_ = text_.replace(org, rep, 1)
        result.append(text_)
    return result


@app.route(
    #
    '/add',
    methods=['POST', 'GET'],
)
def add(
):
    if request.method == 'POST':
        syn_a = request.form.get('syn_a')
        syn_b = request.form.get('syn_b')
        is_inc = int(request.form.get("is_inc")) == 1
        add_ixnclude(syn_a, syn_b, is_inc)
    return render_template("add.html")


@app.route(
    #
    '/',
    methods=['POST', 'GET'],
)
def translator(
):
    if request.method == 'POST':
        lengths = request.form.get('lengths', "876")
        lengths_ = [int(x) for x in lengths.split(",")]
        text = request.form.get('text')
        can_rep = request.form.get('can_rep')
        suggs = {}
        for length in lengths_:
            suggs[length] = g_suggs(text, length, can_rep)
        return render_template("index.html", suggs=suggs, text=text, lengths=lengths, can_rep=can_rep)
    elif request.method == "GET":
        return render_template("index.html", text='', lengths="876,875,874", can_rep='')


if __name__ == "__main__":
    Bootstrap(app)
    app.run(debug=True)
