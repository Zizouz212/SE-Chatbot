# OSData.py

import os
import sys
import requests
import json
import warnings
import datetime
import time

_data_link = "https://api.stackexchange.com/2.2/questions?order=desc&sort=activity&site=opensource&filter=BnUqa25oGUSk0DtHg46BRqrgNQIpP_My.G(tdj_PaN.xIAzk5j"
__doc__ = "Data handling from Stack Exchange API"

# paths
base = os.path.dirname(os.path.abspath(__file__))
data_file = "data.txt"
path = os.path.join(base, "Resources", data_file)

data = None


def init():
    global data
    download_data()
    verified = verify_data()
    
    if not verified:
        warnings.warn("Data not verified.", RuntimeWarning)
        return "I was unable to properly download the data"
    
    info = read_file()
    info = sort_data(info)
    data = info
    return "I've successfully got the data!"


def download_data(link = _data_link, data = path):
    r = requests.get(link)
    with open(data, "w+") as f:
        f.write(r.text.encode('utf-8'))
    r.close()
    return r.text.encode('utf-8')


def verify_data(data = path):
    with open(data, "r") as f:
        info = json.load(f)
    for i in info.iterkeys():
        if i.startswith("error"):
            raise ValueError("Error found")
    return True


def read_file(data = path):
    with open(data, "r") as f:
        info = json.load(f)
    return info


def sort_data(data):

    if data['has_more']:
        warnings.warn("All data not downloaded", RuntimeWarning)

    out = []
        
    info = data['items']

    for i in info:
        out.append(
            {
                'title':         i['title'],
                'link':          i['link'],
                'author':        [i['owner']['display_name'], i['owner']['reputation'], i['owner']['user_id']],       
                'score':         i['score'],
                'views':         i['view_count'],
                'favourites':    i['favorite_count'],
                'tags':          [j for j in i['tags']],
                'creation_date': unicode(datetime.datetime(*time.gmtime(float(i['last_activity_date']))[:6]).strftime('%m %d %Y at %H:%M:%S')),
                'id':            i['question_id'],
                'answer_count':  i['answer_count'],
                'body':          i['body'],
            }
        )
    return out
    

if __name__ == '__main__':
    init()
