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
        "back" : back,
        "flagged" : "false"
    }
    return_document = cardstacks.insert_one(new_document)
    inserted_ok = return_document.acknowledged
    return inserted_ok

@app.route('/add',methods=['POST'])
def add_card():
    is_logged_in = request.cookies.get('loggedin?')
    if is_logged_in == str(os.environ.get('is_logged_in')):
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
        inserted_ok = False
        if all_fields_contain_content:
            db = mongo.db
            cardstacks = db.cardstacks
            s = requests.Session()
            headers = {
                'User-Agent': 'My User Agent 1.0',
                'From': 'youremail@domain.com'  # This is another valid field
            }
            # this route only works locally...
            page = s.get(url, headers=headers)
            soup = BeautifulSoup(page.content, 'html.parser')
            """
            FROM QUIZLET:
                <span class="TermText notranslate lang-en”> term
                <span class="TermText notranslate lang-en”> definition
            """
            terms_defs = soup.findAll("span", {"class": "TermText notranslate lang-en"})
            flashcard_documents = []
            front = None
            if terms_defs:
                for i in range(len(terms_defs)):
                    terms_defs[i] = terms_defs[i].prettify()
                    # grab the content between the <span></span> tags
                    content = terms_defs[i].split("\n")[1:-1]
                    if len(content)>1:
                        content = [c for c in content if c != ' <br/>']
                    content = "".join(content)
                    if not front:
                        # need to do more testing, but it appears there is a leading
                            # space in front of the terms and definitions that needs
                            # to be stripped.
                        front = content[1:]
                    else:
                        # strip the leading space.
                        back = content[1:]
                        new_document = {
                                "Domain" : Domain,
                                "Subdomain" : Subdomain,
                                "Topic" : Topic,
                                "front" : front,
                                "back" : back,
                                "flagged" : "false"
                            }
                        flashcard_documents.append(new_document)
                        front = None
                inserted_ok = cardstacks.insert_many(flashcard_documents).acknowledged
        return render_template('quizlet.html', inserted_ok=inserted_ok)
    else:
        return render_template('login.html')

@app.route('/delete',methods=['GET'])
def get_delete_form():
    is_logged_in = request.cookies.get('loggedin?')
    if is_logged_in == str(os.environ.get('is_logged_in')):
        return render_template('delete.html')
    else:
        return render_template('login.html')

@app.route('/delete',methods=['POST'])
def submit_delete_form():
    is_logged_in = request.cookies.get('loggedin?')
    if is_logged_in == str(os.environ.get('is_logged_in')):

        Domain = request.form.getlist('Domain')[0]
        Subdomain = request.form.getlist('Subdomain')[0]
        Topic = request.form.getlist('Topic')[0]
        all_fields_contain_content = (len(Domain) and
                                     len(Subdomain) and
                                     len(Topic))
        if all_fields_contain_content:
            db = mongo.db
            cardstacks = db.cardstacks
            d = cardstacks.delete_many( {
                   "Domain":Domain,
                   "Subdomain":Subdomain,
                   "Topic":Topic,
                   } )
        return render_template('delete.html')
    else:
        return render_template('login.html')

@app.route('/api/v1/cards',methods=['POST'])
def query_cards():
    db = mongo.db
    cardstacks = db.cardstacks
    # get the subject_data from the returned request.
    # this contains which subjects the user wants flashcards on.
    subject_data = request.get_json()
    filtered_cards = []
    # if a user asks for FLAGGED_CARDS, to avoid duplicates toggle this boolean.
    include_flagged = not any([True if len(string.split("*")) < 2 else False for string in subject_data])
    # iterate through the subject_data
    for string in subject_data:
        # each subject_data entry is a string separated by '*' of:
        # 'Domain*Subdomain*Topic'
        terms_to_match = string.split("*")
        if len(terms_to_match) > 2:
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
                    if include_flagged or card["flagged"] == "false":
                        card = {
                                "Domain" : card["Domain"],
                                "Subdomain" : card["Subdomain"],
                                "Topic" : card["Topic"],
                                "front" : card["front"],
                                "back" : card["back"],
                                "flagged" : card["flagged"]
                                }
                        # add the new card object to the filtered_cards array
                        filtered_cards.append(card)
            # FLAGGED_CARDS
        else:
            cards = cardstacks.find({"flagged":"true"})
            if cards:
                for card in cards:
                    card = {
                            "Domain" : card["Domain"],
                            "Subdomain" : card["Subdomain"],
                            "Topic" : card["Topic"],
                            "front" : card["front"],
                            "back" : card["back"],
                            "flagged" : card["flagged"]
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
    all_domains = cardstacks.distinct('Domain')
    tabs = []
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

    return {'tabs':[{'tabName':'FLAGGED_CARDS'}] + tabs}

@app.route('/api/v1/flagged', methods=['POST'])
def flag_card():
    db = mongo.db
    cardstacks = db.cardstacks

    flagged_card_data = request.get_json()

    if flagged_card_data["flagged"] == True:
        flagged = "true"
    else:
        flagged = "false"
    success = cardstacks.update_one( {
        "Domain":flagged_card_data["Domain"],
        "Subdomain":flagged_card_data["Subdomain"],
        "Topic":flagged_card_data["Topic"],
        "front":flagged_card_data["front"],
        }, {  "$set": { "flagged": flagged }  }).acknowledged
    return { "success": success }

if __name__ == '__main__':
    port = os.getenv("PORT", 7000)
    # app.run(host = '0.0.0.0', port = int(port), debug=True)
    app.run() # might need this if heroku doesn't want me to specify the port.
