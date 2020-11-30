import os

from flask import Flask, render_template, request
app = Flask(__name__)

from flask_cors import CORS, cross_origin
# public API, allow all requests *
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

import requests
from dotenv import load_dotenv

import json

from functools import reduce

import pymongo
from pymongo import MongoClient
# MONGO_URI = str(os.environ.get('MONGO_URI'))
mongo = MongoClient('mongodb://127.0.0.1:27017')

flashcards = {"cards": [{
        "Domain" : "Programming languages",
        "Subdomain" : "C++",
        "Topic" : "Operators",
        "front" : "the front1",
        "back" : "the back1" },
        {
        "Domain" : "Programming languages",
        "Subdomain" : "C++",
        "Topic" : "Operators",
        "front" : "the front1a",
        "back" : "the back1b" },
        {
        "Domain" : "Programming languages",
        "Subdomain" : "C++",
        "Topic" : "Operators",
        "front" : "the front1aa",
        "back" : "the back1bb" },
        {
        "Domain" : "Programming languages",
        "Subdomain" : "C#",
        "Topic" : "Garbage collection",
        "front" : "the front2",
        "back" : "the back2" },
        {
        "Domain" : "Programming languages",
        "Subdomain" : "Python",
        "Topic" : "Decorators",
        "front" : "the front3",
        "back" : "the back3" },
        {
        "Domain" : "Game engines",
        "Subdomain" : "Unity",
        "Topic" : "UI",
        "front" : "the front4",
        "back" : "the back4" },
        {
        "Domain" : "Alcohol",
        "Subdomain" : "Beer",
        "Topic" : "German",
        "front" : "woah",
        "back" : "yay" }
    ]}

subjects = {"tabs":
[
{ 'tabName': "Programming languages", 'content':
[
{
'tabName':"C++",
'content': [
{'tabName':"Operators"},
{'tabName':"Variables"}
]
},
{
'tabName':"Python",
'content': [
{'tabName':"Decorators"},
{'tabName':"Classes"}
]
},
{
'tabName':"C#",
'content': [
{'tabName':"Garbage collection"},
{'tabName':"Variables"}
]
},
]
},
{ 'tabName': "Game engines", 'content':
[
{
'tabName':"Unity",
'content': [
{'tabName':"UI"},
]
},
]
}
]
}

@app.route('/')
def _main():
    # create cardstacks collection and add cards to them
    # (Should each Domain have its own collection? Faster?)
    db = mongo.db
    collection = db.cardstacks
    for i in range(len(flashcards["cards"])):
        Domain = flashcards["cards"][i]["Domain"]
        Subdomain = flashcards["cards"][i]["Subdomain"]
        Topic = flashcards["cards"][i]["Topic"]
        front = flashcards["cards"][i]["front"]
        back = flashcards["cards"][i]["back"]
        new_document = {
            "Domain" : Domain,
            "Subdomain" : Subdomain,
            "Topic" : Topic,
            "front" : front,
            "back" : back
            }
        print(new_document)
        collection.insert_one(new_document)
    print(db.cardstacks.find())
    return render_template('index.html', title='Home',flashcards=flashcards)

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
    app.run(host = '0.0.0.0', port = int(port), debug=True)
    # app.run() // might need this if heroku doesn't want me to specify the port.
