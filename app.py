import os

from flask import Flask, render_template, redirect, request, url_for, make_response
app = Flask(__name__)

from flask_cors import CORS, cross_origin
# public API, allow all requests *
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

from dotenv import load_dotenv

import json

from functools import reduce

from bs4 import BeautifulSoup
import requests
from src.read_cookies import parse_cookies

import pymongo
from pymongo import MongoClient
MONGO_URI = str(os.environ.get('MONGO_URI'))
# mongo = MongoClient('mongodb://127.0.0.1:27017')
mongo = MongoClient(MONGO_URI)

@app.route('/',methods=['GET'])
def _main_get():
    is_logged_in = request.cookies.get('loggedin?')
    if is_logged_in == str(os.environ.get('is_logged_in')):
        return render_template('index.html', Domain='', Subdomain='', Topic='')
    else:
        return render_template('login.html')

@app.route('/login',methods=['POST'])
def login():
    password = request.form.getlist('password')[0]
    password_matches = password == str(os.environ.get('password'))
    response = make_response(redirect(url_for('._main_get')))
    if password_matches:
        response.set_cookie('loggedin?', str(os.environ.get('is_logged_in')))
    return response

@app.route('/logout',methods=['GET'])
def logout():
    response = make_response(render_template('login.html'))
    response.set_cookie('loggedin?', 'nope')
    return response

@app.route('/',methods=['POST'])
def _main_post():
    is_logged_in = request.cookies.get('loggedin?')
    if is_logged_in == str(os.environ.get('is_logged_in')):
        Domain = request.form.getlist('Domain')[0]
        Subdomain = request.form.getlist('Subdomain')[0]
        Topic = request.form.getlist('Topic')[0]
        front = request.form.getlist('front')[0]
        back = request.form.getlist('back')[0]

        # right now inserted_ok is always True
        # inserted_ok = request.headers.get('inserted')
        inserted_ok = True

        return render_template('index.html', Inserted=inserted_ok, Domain=Domain, Subdomain=Subdomain, Topic=Topic)
    else:
        return render_template('login.html')

def add_card_to_db(Domain,Subdomain,Topic,front,back):
    db = mongo.db
    cardstacks = db.cardstacks
    new_document = {
        "Domain" : Domain,
        "Subdomain" : Subdomain,
        "Topic" : Topic,
        "front" : front,
        "back" : back
    }
    return_document = cardstacks.insert_one(new_document)
    inserted_ok = return_document.acknowledged

    return inserted_ok

@app.route('/add',methods=['POST'])
def add_card():
    is_logged_in = request.cookies.get('loggedin?')
    if is_logged_in == str(os.environ.get('is_logged_in')):
        # db = mongo.db
        # cardstacks = db.cardstacks
        Domain = request.form.getlist('Domain')[0]
        Subdomain = request.form.getlist('Subdomain')[0]
        Topic = request.form.getlist('Topic')[0]
        front = request.form.getlist('front')[0]
        back = request.form.getlist('back')[0]

        all_fields_contain_content = (len(Domain) and
                                     len(Subdomain) and
                                     len(Topic) and
                                     len(front) and
                                     len(back))
        inserted_ok = False
        if all_fields_contain_content:
            inserted_ok = add_card_to_db(Domain,Subdomain,Topic,front,back)

        # need to find a way to send along the status of the insertion to _main_post
        # request.headers.set("inserted", inserted_ok)

        return redirect(url_for('._main_post'), code=307)
    else:
        return render_template('login.html')


# web scrape quizlet.com
# must log in first and copy the url path of the flashcards you want.
@app.route('/quizlet',methods=['GET'])
def quizlet_url_form():
    is_logged_in = request.cookies.get('loggedin?')
    if is_logged_in == str(os.environ.get('is_logged_in')):
        return render_template('quizlet.html')
    else:
        return render_template('login.html')


# web scrape quizlet.com
# must log in first and copy the url path of the flashcards you want.
@app.route('/quizlet',methods=['POST'])
def get_flashcards():
    is_logged_in = request.cookies.get('loggedin?')
    if is_logged_in == str(os.environ.get('is_logged_in')):
        Domain = request.form.getlist('Domain')[0]
        Subdomain = request.form.getlist('Subdomain')[0]
        Topic = request.form.getlist('Topic')[0]
        url = request.form.getlist('QuizletURL')[0]
        all_fields_contain_content = (len(Domain) and
                                     len(Subdomain) and
                                     len(Topic) and
                                     len(url))
        if all_fields_contain_content:
            s = requests.Session()
            print(url)
            headers = {
                'User-Agent': 'My User Agent 1.0',
                'From': 'youremail@domain.com'  # This is another valid field
            }
            page = s.get(url,headers=headers)
            soup = BeautifulSoup(page.content, 'html.parser')
            """
            FROM QUIZLET:
                <span class="TermText notranslate lang-en”> term
                <span class="TermText notranslate lang-en”> definition
            """

            terms_defs = soup.findAll("span", {"class": "TermText notranslate lang-en"})

            flashcard = []
            # flashcards = []
            insertion_statuses = []

            if terms_defs:
                for i in range(len(terms_defs)):
                    terms_defs[i] = terms_defs[i].prettify()
                    # grab the content between the <span></span> tags
                    content = terms_defs[i].split("\n")[1]
                    if not len(flashcard):
                        # need to do more testing, but it appears there is a leading
                            # space in front of the terms and defintions that needs
                            # to be stripped.
                        flashcard.append(content[1:])
                    else:
                        front = flashcard[0]
                        # strip the leading space.
                        back = content[1:]
                        # flashcards.append((front,back))
                        inserted_ok = add_card_to_db(Domain,Subdomain,Topic,front,back)
                        insertion_statuses.append(inserted_ok)
                        flashcard = []
        return render_template('quizlet.html', inserted_ok=all(insertion_statuses))
    else:
        return render_template('login.html')

# @app.route('/deleteStack',methods=['DELETE'])
# def delete_cardstack():
#     is_logged_in = request.cookies.get('loggedin?')
#     if is_logged_in == str(os.environ.get('is_logged_in')):
#         return render_template('quizlet.html')
#     else:
#         return render_template('login.html')

@app.route('/api/v1/cards',methods=['POST'])
def query_cards():
    db = mongo.db
    cardstacks = db.cardstacks
    # get the subject_data from the returned request.
    # this contains which subjects the user wants flashcards on.
    subject_data = request.get_json()
    filtered_cards = []
    # iterate through the subject_data
    for string in subject_data:
        # each subject_data entry is a string separated by '*' of:
        # 'Domain*Subdomain*Topic'
        terms_to_match = string.split("*")
        cards = cardstacks.find({
            "Domain":terms_to_match[0],
            "Subdomain":terms_to_match[1],
            "Topic":terms_to_match[2],
            })
        if cards:
            for card in cards:
                # probably a better way to do this, but create a new card object
                    # that does not contain the object id from the database
                    # as this throws an error when returning the filtered_cards
                    # as JSON.
                card = {
                        "Domain" : card["Domain"],
                        "Subdomain" : card["Subdomain"],
                        "Topic" : card["Topic"],
                        "front" : card["front"],
                        "back" : card["back"]
                        }
                # add the new card object to the filtered_cards array
                filtered_cards.append(card)
    # return the filtered cards to the frontend.
    return { "cards": filtered_cards }

@app.route('/api/v1/tabs')
def query_tabs():
    db = mongo.db
    cardstacks = db.cardstacks
    # find all Domain types in the database >
        # then all Subdomains of each Domain > then all topics of each
        # Subdomain.
    # create the appropriate data structure for the frontend so users can query
        # the database with the specific topics they want to study.
    tabs = []
    all_domains = cardstacks.distinct('Domain')
    for i, each_domain in enumerate(all_domains):
        tabs.append({'tabName':each_domain,'content':[]})
        all_subdomains_of_this_domain = cardstacks.find({
                                            "Domain":
                                            each_domain }).distinct('Subdomain')
        for j, each_subdomain in enumerate(all_subdomains_of_this_domain):
            tabs[i]['content'].append({'tabName':each_subdomain,'content':[]})
            all_topics_of_this_subdomains = cardstacks.find({
                                                "Domain":
                                                each_domain,
                                                "Subdomain":
                                                each_subdomain,
                                                }).distinct('Topic')
            for each_topic in all_topics_of_this_subdomains:
                tabs[i]['content'][j]['content'].append({'tabName':each_topic})

    return {'tabs':tabs}

if __name__ == '__main__':
    port = os.getenv("PORT", 7000)
    # app.run(host = '0.0.0.0', port = int(port), debug=True)
    app.run() # might need this if heroku doesn't want me to specify the port.
