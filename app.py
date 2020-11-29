import os

from flask import Flask, render_template, request
app = Flask(__name__)

from flask_cors import CORS, cross_origin
# public API, allow all requests *
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

import requests
from dotenv import load_dotenv

import json

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
        "back" : "the back4" }
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
    # (Should each Domain have its own collection?)
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

@app.route('/api/v1/test/cards',methods=['POST'])
def testAPI_cards():
    db = mongo.db
    collection = db.cardstacks

    # get the subject data from the returned request
    subject_data = request.get_json()
    print(subject_data)

    # create a lookup dictionary
    LOOKUP = {0:"Domain",1:"Subdomain",2:"Topic",3:"Match"}

    # iterate through the subject_data
    filtered_cards = []
    for string in subject_data:
        # each subject_data entry is a string separated by '*' of:
        # Domain*Subdomain*Topic
        terms_to_match = string.split("*")
        # Future: Pull from the database the correct cardstacks based on the
            # terms_to_match: ['Domain', 'Subdomain', 'Topic'.
        cards = collection.find({
            "Domain":terms_to_match[0],
            "Subdomain":terms_to_match[1],
            "Topic":terms_to_match[2],
            })
        if cards:
            for card in cards:
                card = {
                        "Domain" : card["Domain"],
                        "Subdomain" : card["Subdomain"],
                        "Topic" : card["Topic"],
                        "front" : card["front"],
                        "back" : card["back"]
                        }
                filtered_cards.append(card)
        # Presently: iterate through the simulated card array and append to the
            # filtered_cards array
        # i = 0
        # for card in flashcards["cards"]:
        #     while i < 3 and terms_to_match[i] == card.get(LOOKUP[i],None):
        #         i+=1
        #     if i == 3:
        #         filtered_cards.append(card)
        #     i = 0
    # return the filtered cards to the frontend.
    print(filtered_cards)
    return {"cards":filtered_cards}

@app.route('/api/v1/test/tabs')
def testAPI_tabs():
    return subjects

if __name__ == '__main__':
    port = os.getenv("PORT", 7000)
    app.run(host = '0.0.0.0', port = int(port), debug=True)
    # app.run() // might need this if heroku doesn't want me to specify the port.
