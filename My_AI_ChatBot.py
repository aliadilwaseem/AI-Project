
import queue
import token
from urllib import response 
import nltk
from flask import Flask, render_template, request, redirect, url_for
from nltk.tokenize import sent_tokenize, word_tokenize
import aiml, os
from autocorrect import spell
from bs4 import BeautifulSoup
import requests, re
from nltk.corpus import wordnet
import pytholog


app = Flask(__name__)

BRAIN_FILE="./pretrained_model/aiml_pretrained_model.dump"
k = aiml.Kernel()

#if os.path.exists(BRAIN_FILE):
#    print("Loading from brain file: " + BRAIN_FILE)
#    k.loadBrain(BRAIN_FILE)
#else:
#    print("Parsing aiml files")
k.bootstrap(learnFiles="./pretrained_model/learningFileList.aiml", commands="load aiml")
    #print("Saving brain file: " + BRAIN_FILE)
    #k.saveBrain(BRAIN_FILE)

knowledge_base = pytholog.KnowledgeBase('KB')
knowledge = [
    'father(X, Y):- male(X), parent(X, Y)',
    'mother(X, Y):- female(X), parent(X, Y)',
    'child(X, Y):- parent(Y, X)'
]
knowledge_base(knowledge)

print('_'*60)
# resetting predicates
k.respond('reset questions', 'user1')
k.respond('reset facts', 'user1')

def set_fact(fact, value, value2=None):
    if value2:
        new_fact = fact + '(' + value.lower() + ',' + value2.lower() + ')'
    else:
        new_fact = fact + '(' + value.lower() + ')'

    knowledge.insert(0, new_fact)
    knowledge_base(knowledge)
    k.respond('reset facts', 'user1')


def query_kb(fact, value):
    k.respond('reset questions', 'user1')
    query = fact + '(X, ' + value.lower().strip() + ')'
    result = knowledge_base.query(pytholog.Expr(query))

    response = ''
    for value in result:
        try:
            response += value['X'].title() + ', '
        except:
            return None
    
    return response[:-2]


def preprocess_input(input_text):
    token = word_tokenize(input_text)
    return preprocess_input

@app.route('/')
def home():
    return render_template('HTMLPage2.html')

@app.route('/signin', methods=['POST', 'GET'])
def signin():
    email = request.form.get('email')
    password = request.form['password']

    print(email, password, 'from user')
    if email == "admin@umt.com" and password == "password":
        print('success')
        return redirect(url_for('chatbot'))

    else:
        print('failed')
        return "Login Failed"
    
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    confirmpassword = request.form.get('confirm_password')



    if password != confirmpassword:
        return "Password do not match"
    else:
        return "Signup Successfull"

@app.route("/chatbot")
def chatbot():
    return render_template("home.html")


def check_predicates():
    male = k.getPredicate('male', 'user1')
    female = k.getPredicate('female', 'user1')
    parent = k.getPredicate('parent', 'user1')
    child = k.getPredicate('child', 'user1')
    father_of = k.getPredicate('father_of', 'user1')
    mother_of = k.getPredicate('mother_of', 'user1')
    child_of = k.getPredicate('child_of', 'user1')

    result = None

    if male != '':
        set_fact('male', male)
    elif female != '':
        set_fact('female', female)
    elif parent != '':
        set_fact('parent', parent, child)
    elif father_of != '':
        result = query_kb('father', father_of)
    elif mother_of != '':
        result = query_kb('mother', mother_of)
    elif child_of != '':
        result = query_kb('child', child_of)
    
    return result

def scrap(word):
    word = word.title()
    a = word.split()
    word = "_".join(a)

    url = 'https://en.wikipedia.org/wiki/'+word
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    para = soup.select('div.mw-parser-output')
    paras = []
    for element in para:
        paragraphs = element.find_all('p', class_ = False)
        paras.extend(paragraphs)

    try:
        data = paras[0].text
    except IndexError:
        return None

    final = data
    if final == '\n':
        return None
    
    return final



def get_synonyms(word):
    synonyms = []
    for synset in wordnet.synsets(word):
        for lemma in synset.lemmas():
            synonyms.append(lemma.name())
    return set(synonyms)




@app.route("/get")
def get_bot_response():
    query = request.args.get('msg')
    #query = [spell(w) for w in (query.split())]
    #question = " ".join(query)
    #print("question",question)
    response = k.respond(query)
    word = k.getPredicate("search")
    #wn = k.getPredicate("synonyms")
    prolog = check_predicates()
    
    if word != '' :
        defi = scrap(word)
        k.setPredicate("search_results",defi)
        k.setPredicate("search", '')
        updatedresponse = k.respond(query)

        return str(updatedresponse)

    elif word == '':
        word_net = get_synonyms(word)
        k.setPredicate("findings",word_net)
        k.setPredicate("synonyms",'')
        upresponse = k.respond(query)

        return str(upresponse)
    elif prolog:
        return prolog

    elif response != '':
        return str(response)
    else:
        return "Sorry!, I don't have answer for that"
    #print("response",response)
    #if response:
    #    return (str(response))
    #else:
    #    return (str("I don't have answer for that. Sorry"))
    #    e
#while True:
#    text = input("Human: ")
#    if text == "Bye":
#        break
#    else:
#        response = myBot.respond(text,"Ali")
#        tokens = word_tokenize(response)
#        nltk.pos_tag(tokens)
#        print("Bot : ", tokens)           
        
if __name__ == "__main__":
    # app.run()
    app.run(host='0.0.0.0', port='5000')