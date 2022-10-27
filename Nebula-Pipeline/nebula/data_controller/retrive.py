#By Theo Long
#This is a code for retriving data from es
#date: 7/13/2016

#import pipeline
from elasticsearch import Elasticsearch

es = Elasticsearch()

def search(target_index, target):
    #result= es.search(index=target_index, body={"query": {"match" : { "text" : target }}})
    BODY={"query": {
        "match": {
            "text": {
                "query": target,
                "minimum_should_match": "80%"
            }
        }
    }}
    
    result= es.search(index=target_index, body=BODY)
    result = result
    return result

if __name__ == "__main__":
    while True:
    	searchList=[]

    	target=input("target: ")
        try:
            result= search('test_index', target)
            hits=result['hits']['total']
            print(hits)
            if hits != 0:
                for i in result['hits']['hits']:
                    print("===============================")
                    print(i['_id'])
            break
        except ValueError:
            print("Oops!  search error, make sure you have the index")