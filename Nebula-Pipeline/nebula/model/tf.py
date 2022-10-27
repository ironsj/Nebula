#term frequency
#
import nebula.pipeline as pipeline
import operator
import re

from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer


class TFModel(pipeline.Model):
    def __init__(self):
        self._MaxAttri=6
        pass

    def forward_input_reqs(self):
        return [pipeline.DOC_ID, pipeline.RAW_TEXT]
    
    def forward_output(self):
        return [pipeline.DOC_ATTRIBUTES]
    
    def inverse_input_reqs(self):
        return [pipeline.INTERACTION]

    def setup(self, data):
        pass

    def forward(self, data):
	if pipeline.DOCUMENTS in data:
            for doc in data[pipeline.DOCUMENTS]:
                freq = {}
                maxi = 0.0;
                raw_text = self.filterStopWord(doc[pipeline.RAW_TEXT])
                
                for w in raw_text.split():
                    if w not in freq:
                        freq[w] =1.0
                    else:
                        freq[w] += 1.0
                    if freq[w] > maxi:
                        maxi = freq[w]
		    if pipeline.ATTRIBUTES not in data:
                        data[pipeline.ATTRIBUTES] = {}
		    if pipeline.SIMILARITY_WEIGHTS not in data:
			data[pipeline.SIMILARITY_WEIGHTS] = {}
		    #print "printing attributes" + str(data[pipeline.ATTRIBUTES])
                    if w not in data[pipeline.ATTRIBUTES]:
			data[pipeline.ATTRIBUTES][w] = len(data[pipeline.ATTRIBUTES])
		    if w not in data[pipeline.SIMILARITY_WEIGHTS]:
			newWeight = float(1.0/(len(data[pipeline.SIMILARITY_WEIGHTS])+1))
			print("=============== new SIMILARITY_WEIGHTS: " + str(newWeight) + " length: " + str(len(data[pipeline.SIMILARITY_WEIGHTS])+1))
			data[pipeline.SIMILARITY_WEIGHTS][w] = newWeight
			for key in data[pipeline.SIMILARITY_WEIGHTS]:
			    data[pipeline.SIMILARITY_WEIGHTS][key] = newWeight
			    #print data[pipeline.SIMILARITY_WEIGHTS][key]
		for key in freq:
                    freq[key] = freq[key]/maxi
                    #print "freq: " + str(freq[key]/maxi)
		doc[pipeline.DOC_ATTRIBUTES] = freq
	#if pipeline.ATTRIBUTES in data:
	#    print "========= printing attributes" + str(data[pipeline.ATTRIBUTES])	
	#if pipeline.SIMILARITY_WEIGHTS in data:
	#    print "========= printing SIMILARITY_WEIGHTS" + str(data[pipeline.SIMILARITY_WEIGHTS])	
		

    def inverse(self, data):
        if pipeline.ATTRIBUTE_RELEVANCE_DELTA in data:
            freq = data[pipeline.ATTRIBUTE_RELEVANCE_DELTA]
            sorted_f = sorted(list(freq.items()), key=operator.itemgetter(1), reverse=True)
            if len(sorted_f) <= self._MaxAttri:
                sorted_f=sorted_f
            else:
                sorted_f=sorted_f[:self._MaxAttri]
            searchList=""
            for key,value in sorted_f:
                searchList = searchList + " " + key
            
            data["query"] = searchList
            #return sorted_f
            
    def filterStopWord(self,sentence):
        blacklist=[]
        sentence = sentence.lower()
        sentence = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', sentence)
        sentence = re.sub(r"#(\w+)", '', sentence)
        sentence = re.sub(r"@(\w+)", '', sentence)
        tokenizer = RegexpTokenizer(r'\w+')
        tokens = tokenizer.tokenize(sentence)
        allbadwords = stopwords.words('english') + blacklist
        filtered_words = [w for w in tokens if not w in allbadwords]
        raw_text = " ".join(filtered_words)
        return raw_text
