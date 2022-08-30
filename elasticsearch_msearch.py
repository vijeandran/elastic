from elasticsearch import Elasticsearch
import json

def msearch():
    es = Elasticsearch()

    search_arr = []
    search_arr.append({"index": "emp_details_new"})
    search_arr.append({ "_source": ["id", "licence_num"], "min_score": 0.5, "query": { "multi_match": { "query": "861", "fields": ["licence_num"], "type": "phrase_prefix" } }})

    search_arr.append({"index": "emp_details_new"})
    search_arr.append({ "_source": ["id", "phone"], "min_score": 0.5, "query": { "multi_match": { "query": "861", "fields": ["phone"], "type": "phrase_prefix" } }})

    request = ''

    for each in search_arr:
        request += '%s \n' %json.dumps(each)

    resp = es.msearch(body = request)
    print(resp)

msearch()