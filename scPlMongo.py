from typing import Optional,List
from fastapi import FastAPI,Query
from pydantic import BaseModel,Field, EmailStr
from pymongo import MongoClient, UpdateOne
from passlib.context import CryptContext
import requests
from bs4 import BeautifulSoup
from string import punctuation
from bson import ObjectId
import re


#filtering library
import nltk
nltk.download('punkt')
from nltk.corpus import stopwords  
from nltk.stem import PorterStemmer

porter=PorterStemmer()

def increase_word_count(word_list):
    wordcount={}
    for word in word_list:
        if(word in wordcount):
            wordcount[word]=wordcount[word]+1
        else:
            wordcount[word]=1
    for word in wordcount.keys():
        result=db.words_count.find_one({'word':word})
        if(result):
            db.words_count.update_one({'word':word},{"$inc":{'count':wordcount[word]}})
        else:
            db.words_count.insert_one({'word':word, 'count':wordcount[word]})


def filter_sentence(input_str):
    stop_words = set(stopwords.words('english'))  
    word_tokens = nltk.word_tokenize(input_str)
    word_tokens=[porter.stem(w) for w in word_tokens if not w in punctuation]
    filtered_sentence = [w for w in word_tokens if not w in stop_words]
    increase_word_count(filtered_sentence)   
    filtered_sentence=set(filtered_sentence)
    return ' '.join(filtered_sentence)
    


URL="https://thehackernews.com/"

app = FastAPI()

client = MongoClient("mongodb-server", 27017)
db = client.assignment

page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')
for post in soup.find_all(class_='story-link'):
    TB=post.find(class_='home-title')
    DB=post.find(class_='home-desc')
    UB=post
    IB=post.find(class_='home-img-src')
    if TB and DB and UB and IB:
        if(db.meta_data.find_one({'URL':UB['href']})):
            continue
        filtered_text=filter_sentence(DB.text.lower())
        metaData=db.meta_data.insert_one({
            'URL':UB['href'],  
            'Description': DB.text,
            'Image':IB['data-src'],
            'Filtered_description': filtered_text
        })
        db.post.insert_one({
            'URL':UB['href'],
            'Title': TB.text,  
            'Meta_data': ObjectId(metaData.inserted_id)
        })


# @app.get("/hackernews")
# def get_news():
#     allpost=[]
#     for post in db.post.find():
#         metadata=db.meta_data.find_one({"_id":post['Meta_data']})
#         allpost.append({
#             'URL':post['URL'],
#             'Title':post['Title'],
#             'Meta_data':{
#                 'Description':metadata['Description'],
#                 'Image':metadata['Image']
#             }
#         })
#     return allpost


@app.get("/hackernews")
def get_news(searchstr:str=Query("")):
    soln=set([])
    for data in db.meta_data.find():
        soln.add(data['URL'])
    for word in searchstr.split():
        if word in punctuation:
            continue
        tempSoln=set([])
        regx = re.compile(word, re.IGNORECASE)
        for data in db.meta_data.find({"Description":regx}):
            tempSoln.add(data['URL'])
        soln.intersection_update(tempSoln)
    return list(soln)

