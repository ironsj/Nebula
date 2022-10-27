#By Theo Long
#This is a code specifically for readin file from cresent into es
#date: 7/13/2016
from nebula import pipeline
import operator
import os
import glob
import sys
import re
from datetime import datetime
from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
import requests
import json
import re
if __name__ == "__main__":
	count=0
	raw_docs = []
	#open files====================================================
	path = '../../crescent_raw/'  # This path may have to change due to the new code refactors
	listing = os.listdir(path)

	es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
	for infile in listing:
		if "txt" in infile:
			with open(path+infile, "r") as myfile:
				count+=1
				doc = {
				    'author': 'unknown',
				    'text': myfile.read(),
				    'timestamp': datetime.now(),
				}
				infile=re.sub('\.txt$', '', infile)
				es.index(index='test_index', doc_type='reports', id=infile, body=doc)
				print(infile)