import csv
import os
import re
import numpy as np

from nebula import pipeline


__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))



class TwoView_CSVDataController(pipeline.DataController):
    """This basic implementation of a data controller implements basic text
    queries for new documents. It loads a CSV file of data and compares text
    searches to the document names and puts all matching documents in the
    working set. It also accesses the raw data through the raw_folder
    argument, which should have a file named <id>.txt for each document
    ID in the CSV file.
    
    csvfile: the filename of the CSV file to load
    raw_folder: the folder name of the folder containing the raw documents
    """
    def __init__(self, csvfile, raw_folder=None):
        self._documents = []
        self._attributes_set = []
        self._columns = []
        self._rows = []
        self._attributes = {}
        self._attr_documents = {}
        self._raw_folder = raw_folder
        
        attrs_high_d = []
        with open(csvfile, "rU") as f:
            reader = csv.reader(f)
            self._columns = next(reader)[1:]
            for i in range(len(self._columns)):
                self._attributes[self._columns[i]] = i
                
            numCols = -1   
            for i,line in enumerate(reader):
                if numCols == -1:
                        numCols = len(line)
                if len(line) == numCols:
                    doc = {}
                    doc[pipeline.DOC_ID] = line[0]
                    self._attr_documents[line[0]]=i
                    self._rows.append(line[0])
                    doc[pipeline.HIGHD_POSITION] = [float(x) for x in line[1:]]
                    attrs_high_d.append(doc[pipeline.HIGHD_POSITION])
                    doc[pipeline.DOC_ATTRIBUTES] = {self._columns[i]: float(line[i+1]) for i in range(len(self._columns))}
                    self._documents.append(doc)
                
            attrs_high_d = np.array(attrs_high_d)
            #TF-IDF values for Attribute View (transpose of TF-IDF values for documents)
            attrs_high_d = attrs_high_d.T
            
            for i, attr in enumerate(attrs_high_d):
                attrs = {}
                attrs[pipeline.ATTRIBUTE_ID] = self._columns[i]
                attrs[pipeline.HIGHD_POSITION] = list(attr)
                attrs[pipeline.ATTRIBUTE_DOCS] = {self._rows[k]:float(attr[k]) for k in range (len(self._rows))}
                self._attributes_set.append(attrs)
        
        max_attributes = {}
        min_attributes = {}
        for doc in self._documents:
            for attr, value in doc[pipeline.DOC_ATTRIBUTES].items():
                if attr not in max_attributes or value > max_attributes[attr]:
                    max_attributes[attr] = value
                if attr not in  min_attributes or value < min_attributes[attr]:
                    min_attributes[attr] = value
                              
        for doc in self._documents:
            for attr in doc[pipeline.DOC_ATTRIBUTES]:
                denomonator = max_attributes[attr] - min_attributes[attr]
                if denomonator != 0:
                    doc[pipeline.DOC_ATTRIBUTES][attr] = (doc[pipeline.DOC_ATTRIBUTES][attr] - min_attributes[attr]) / denomonator
                else:
                    doc[pipeline.DOC_ATTRIBUTES][attr] = 0
                    
        max_docs = {}
        min_docs = {}
        for attr in self._attributes_set:
            for doc in self._documents:
                value = doc[pipeline.DOC_ATTRIBUTES][attr[pipeline.ATTRIBUTE_ID]]
                if doc[pipeline.DOC_ID] not in max_docs or value > max_docs[doc[pipeline.DOC_ID]]:
                    max_docs[doc[pipeline.DOC_ID]] = value
                if doc[pipeline.DOC_ID] not in min_docs or value < min_docs[doc[pipeline.DOC_ID]]:
                     min_docs[doc[pipeline.DOC_ID]] = value
  
        for attr in self._attributes_set:
            for doc in self._documents:
                value = doc[pipeline.DOC_ATTRIBUTES][attr[pipeline.ATTRIBUTE_ID]]
                doc = doc[pipeline.DOC_ID]
                denomonator = max_docs[doc] - min_docs[doc]
                if denomonator != 0:
                    attr[pipeline.ATTRIBUTE_DOCS][doc] = (value - min_docs[doc]) / denomonator
                else:
                    attr[pipeline.ATTRIBUTE_DOCS][doc] = 0
        
      
              
    def input_reqs(self):
        return set([pipeline.INTERACTION])
    
    def output(self):
        return set([pipeline.DOC_ID, pipeline.HIGHD_POSITION, pipeline.DOC_ATTRIBUTES, pipeline.ATTRIBUTES])
            
    def get(self, args):
        """Accepts two requests:
        
        "attributes" returns a list of attribute names for the underlying data
        "raw" returns the raw text for a single document based on an "id"
        """
        if "type" not in args:
            return None
        
        def get_attributes():
            for doc in self._documents:
                if doc[pipeline.DOC_ID] == args["id"]:
                    args["value"] = doc[pipeline.DOC_ATTRIBUTES]
                    return args
            for attr in self._attributes_set:
                if attr[pipeline.ATTRIBUTE_ID] == args["id"]:
                    args["value"] = attr[pipeline.ATTRIBUTE_DOCS]
                    return args
        
        req_type = args["type"]
        if req_type == "attributes":
            if "id" in args:
                return get_attributes()
            else:
                args["value"] = self._columns
                return args
            
        elif req_type == "raw" and self._raw_folder:
            if (os.path.isfile(os.path.join(self._raw_folder, args["id"] + ".txt"))):
                for doc in self._documents:
                    if doc[pipeline.DOC_ID] == args["id"]:
                        with open(os.path.join(self._raw_folder, args["id"] + ".txt"), "r") as f:
                            args["value"] = f.read()
                            return args
                    
                for attr in self._attributes_set:
                    if attr[pipeline.ATTRIBUTE_ID] == args["id"]:
                        with open(os.path.join(self._raw_folder, args["id"] + ".txt"), "r") as f:
                            args["value"] = f.read()
                            return args
            else:
                if "id" in args:
                    return get_attributes();
                    
                   
                      
        return None

    def setup(self, data):
        """Passes the attribute mapping and document list down the setup."""
        #Data for document View ( attributes / Dictionary of Documents)
        data[pipeline.ATTRIBUTES] = self._attributes
        data[pipeline.DOCUMENTS] = self._documents
        
        #Data for attribute view (Documents / Dictionary of Attributes
        data[pipeline.DOCUMENTS_LIST] = self._attr_documents
        data[pipeline.ATTRIBUTE_LIST] = self._attributes_set
        
        
            
    def run(self, data):
        """Searches for new documents based on two methods. If a set of
        attribute weights are found, those are used to find the most relevant
        documents to return. Otherwise, if a search query is found, that query
        is used to find a regex match against any documents. This all should
        be redundant since all documents are passed down upon load to a presumed
        relevance based model, such as the ActiveSetModel."""
        search_relevance = {}
        if pipeline.ATTRIBUTE_RELEVANCE in data:
            # It's an attribute search, so use the weighted attributes to find
            # documents to send down
            for attr in data[pipeline.ATTRIBUTE_RELEVANCE]:
                weight = data[pipeline.ATTRIBUTE_RELEVANCE][attr]
                if weight > 0 and attr in self._attributes:
                    search_relevance[attr] = weight
                    
            
        elif pipeline.INTERACTION in data and data[pipeline.INTERACTION] == "search":
            term = data["query"]
            prog = re.compile(term, flags=re.IGNORECASE)
            
            for attr in self._attributes:
                if prog.search(attr):
                    # Give each matching attribute a weight of one, so 
                    # documents with that term will be sent down
                    search_relevance[attr] = 1
                        
        if len(search_relevance) == 0:
          
            return {}    
                    
        return_documents = []
        for doc in self._documents:
            relevance = self._relevance(doc, search_relevance)
            if relevance > 0:
                return_documents.append(doc)
                
        return { pipeline.DOCUMENTS: return_documents }
            
        
    def _relevance(self, doc, attr_weights):
        """Calculates the relevance for a single document."""
        relevance = 0
        for attr in attr_weights:
            attr_val = doc[pipeline.HIGHD_POSITION][self._attributes[attr]]
            relevance += attr_weights[attr] * attr_val
            
        return relevance