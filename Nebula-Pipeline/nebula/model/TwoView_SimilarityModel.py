# -*- coding: utf-8 -*-
import itertools
import json
import os
import subprocess

import numpy as np
from sklearn.manifold import MDS
from scipy.stats.mstats import zscore

import nebula.pipeline as pipeline

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

# The list of documents passed through the forward pipeline
from nebula.pipeline import DOCUMENTS
# The ID of each document with the document list
from nebula.pipeline import DOC_ID
# The high dimensional position of each document within the list
#from nebula.pipeline import HIGHD_POSITION
# A map of attributes for a document. Alternative way of storing position
from nebula.pipeline import DOC_ATTRIBUTES
# The low dimensional position of each document within the list
from nebula.pipeline import LOWD_POSITION
# The relevance of each document within the list
#from nebula.pipeline import DOC_RELEVANCE
# A set of attribute names that exist in the data
#from nebula.pipeline import ATTRIBUTES
# A dictionary of attribute weights
#from nebula.pipeline import ATTRIBUTE_RELEVANCE
# A dictionary of attribute weight deltas from the most recent interaction
#from nebula.pipeline import ATTRIBUTE_RELEVANCE_DELTA
# A list of weights for the similarity of attributes
from nebula.pipeline import SIMILARITY_WEIGHTS
# An interaction, whose value is a string specifying the type of interaction
from nebula.pipeline import INTERACTION

from nebula.pipeline import VIEW
from nebula.pipeline import ATTRIBUTE_LIST
#from nebula.pipeline import DOCUMENTS_LIST
from nebula.pipeline import ATTRIBUTE_ID
from nebula.pipeline import ATTRIBUTE_DOCS

from .DistanceFunctions import euclidean, cosine




class TwoView_SimilarityModel(pipeline.Model):
    """A similarity model contains weights for each dimension in high
    dimensional space of the data. It takes in the positions of each point
    in this high dimensional space, and outputs a pairwise distance matrix.
    Any of the predefined distance functions can be used, or a custom one
    can be supplied.
    """
    
    params = {"low_dimensions": "Num Low Dimensions",
              "dist_func": "Distance Function"}
    
    def __init__(self, dist_func="euclidean", low_dimensions=2):
        self.dist_func = dist_func
        self.low_dimensions = low_dimensions
        
        self._weights = {}
        self._attrs_weights = {}
        self._docs_weights = {}
        self._docs = []
        self._attrs = []
        self._high_d = {}
        self._attr_high_d ={}
        self._new_docs = False
        self._new_weights = False 
        self._interaction = ""
        self._view = True
        

    def forward_input_reqs(self):
        return [DOC_ATTRIBUTES]
    
    def forward_output(self):
        return [LOWD_POSITION, SIMILARITY_WEIGHTS]
    
    def inverse_input_reqs(self):
        return [INTERACTION]
    
    def setup(self, data):
        # Store all the documents at the start
        if DOCUMENTS and ATTRIBUTE_LIST in data:
            self._update_documents(data[DOCUMENTS])
            self._update_attributes(data[ATTRIBUTE_LIST])
        
                    
    
    def _update_documents(self, docs):
        # If the documents are the same as last time, we don't need to
        # update, unless the weights changed
        # Kinda complicated currently, can I simplify this?
        if len(self._docs) == len(docs):
            found = False
            for new_doc in docs:
                found = False
                for old_doc in self._docs:
                    if new_doc[DOC_ID] == old_doc[DOC_ID]:
                        found = True
                        break
                    
                if not found:
                    break
            if not found:
                self._new_docs = True
        else:
            self._new_docs = True
        
        if self._new_docs:
            # Make a copy of the document ID's and high dimensional positions    
            self._docs = [{DOC_ID: x[DOC_ID], DOC_ATTRIBUTES: x[DOC_ATTRIBUTES]} for x in docs]
    
            
    def _update_attributes(self, attrs):
        # If the documents are the same as last time, we don't need to
        # update, unless the weights changed
        # Kinda complicated currently, can I simplify this?
        
        
        if len(self._attrs) == len(attrs):
            found = False
            for new_attr in attrs:
                found = False
                for old_attr in self._attrs:
                    if new_attr[ATTRIBUTE_ID] == old_attr[ATTRIBUTE_ID]:
                    
                        found = True
                        break
                    
                if not found:
                    break
            if not found:
                self._new_attrs = True
        else:
            self._new_attrs = True
        
        
        if self._new_attrs:
            # Make a copy of the attribute ID's and high dimensional positions   
            self._attrs  = [{ATTRIBUTE_ID: x[ATTRIBUTE_ID], ATTRIBUTE_DOCS: x[ATTRIBUTE_DOCS]} for x in attrs]
         
           
    
    def _vectorize(self, docs):
        """Forms a high dimensional position matrix and weight vector for the 
        documents based on their attribute mappings. The columns in the matrix
        correspond to the entries in the weight vector"""
        num_docs = len(docs)
        
        # Form the set of all attributes to form the matrix
        attributes = set(self._weights)
                
        attribute_list = list(attributes)
        high_d = np.zeros((num_docs, len(attributes)), dtype=np.float64)
        
        #need to change this
        # Fill in the highD matrix with the attribute values of the documents
        for i in range(num_docs):
            for j in range(len(attribute_list)):
                if attribute_list[j] in docs[i][DOC_ATTRIBUTES]:
                    high_d[i][j] = docs[i][DOC_ATTRIBUTES][attribute_list[j]]
        
        # If there is 0 variability, we will get nan's, and that's fine
        with np.errstate(divide="ignore", invalid="ignore"):
            # Calculate the zscore of the high D data, don't normalize
            high_d = zscore(high_d)
        
        # In case any dimensions have 0 variability
        high_d = np.nan_to_num(high_d)

        # Make a list of weights to use for the distance calculation
        # The new set of weights should still sum to 1
        old_attribute_count = len(self._weights)
        print("Old attr count: %d, New count: %d" % (old_attribute_count, len(attribute_list)))
        print("Old weight of attrs sum: %f" % np.sum(list(self._weights.values())))
        
        weight_list = []
        for attr in attribute_list:
            if attr in self._weights:
                weight_list.append((attr, self._weights[attr]))
            else:
                weight_list.append((attr, 0))
        
        print("Attr weight sum: %f" % np.sum(list(self._weights.values())))
                        
        return (high_d, weight_list)

    def _attr_vectorize(self, attrs):
        """Forms a high dimensional position matrix and weight vector for the 
        attributes based on their documents mappings. """
        num_attrs = len(attrs)
        
        # Form the set of all documents to form the matrix
        documents = set(self._docs_weights)
                
                
        document_list = list(documents)
        high_d = np.zeros((num_attrs, len(documents)), dtype=np.float64)
        
        #need to change this
        # Fill in the highD matrix with the attribute values of the documents
        for i in range(num_attrs):
            for j in range(len(document_list)):
                if document_list[j] in attrs[i][ATTRIBUTE_DOCS]:
                    high_d[i][j] = attrs[i][ATTRIBUTE_DOCS][document_list[j]]
                    
        # If there is 0 variability, we will get nan's, and that's fine
        with np.errstate(divide="ignore", invalid="ignore"):
        # Calculate the zscore of the high D data, don't normalize
            high_d = zscore(high_d)
            
        # In case any dimensions have 0 variability
        high_d = np.nan_to_num(high_d)
                
        # Make a list of weights to use for the distance calculation
        # The new set of weights should still sum to 1
        old_documents_count = len(self._docs_weights)
        print("Old doc count: %d, New count: %d" % (old_documents_count, len(document_list)))
        print("Old weight of docs sum: %f" % np.sum(list(self._docs_weights.values())))
        
        weight_list = []
        for doc in document_list:
            if doc in self._docs_weights:
                weight_list.append((doc, self._docs_weights[doc]))
            else:
                weight_list.append((doc, 0))
        
        print("Doc weight sum: %f" % np.sum(list(self._docs_weights.values())))
        
        return (high_d, weight_list)

    
    def _pairwise_distance(self, high_d, weight_list):
        """Calculate a weighted pairwise distance matrix for the high 
        dimensional positions."""
        num_docs = len(high_d)
        
        # Compute the pairwise distance of the high dimensional points
        pdist = np.zeros((num_docs, num_docs), dtype=np.float64)
        weight_list = [x[1] for x in weight_list]
        # Calculate the distance between every pair of points
        dist_func = euclidean
        if self.dist_func == "cosine":
            dist_func = cosine
        for i in range(0, num_docs - 1):
            for j in range(i + 1, num_docs):
                d = dist_func(high_d[i], high_d[j], weight_list)
                pdist[i][j] = d
                pdist[j][i] = d
                
        return pdist
     
    def _reduce(self, pdist, dimensions=2):
        """Run MDS on the pairwise distances. If you want to alter the forward 
        MDS algorithm, do it here!"""
        mds = MDS(n_components=self.low_dimensions, dissimilarity="precomputed", n_init = 10, max_iter=900, random_state=0)
        mds.fit(pdist)
        return mds.embedding_
    
    def forward(self, data):   
        
        
        self._attrs_weights = pipeline.Model.global_attribute_weight_vector
        self._docs_weights = pipeline.Model.global_document_weight_vector
        self._weights = pipeline.Model.global_attribute_weight_vector


        if (self._interaction != "none" and "view" in data): 
            self._view = data["view"]
           
        """Data blob passed from pipeline to node.js server. The data blob has two dictionaries (ATTRIBUTE/OBSERVATION). 
        Each dictionary has normalized raw data, low dimension position, simialrity weight vector, and id of each attribute or observation  """
        data["ATTRIBUTE"] ={}
        data["OBSERVATION"]={}  
        if DOCUMENTS and ATTRIBUTE_LIST in data:
            self._update_documents(data[DOCUMENTS])
            self._update_attributes(data[ATTRIBUTE_LIST])
            data["ATTRIBUTE"][ATTRIBUTE_LIST] = data[ATTRIBUTE_LIST]
            data["OBSERVATION"][DOCUMENTS] = data[DOCUMENTS]
        else:
            # Set the documents to our last copy to continue the forward model
            data["ATTRIBUTE"][ATTRIBUTE_LIST] = [{ATTRIBUTE_ID: x[ATTRIBUTE_ID], ATTRIBUTE_DOCS: x[ATTRIBUTE_DOCS]} for x in self._attrs]  
            data["OBSERVATION"][DOCUMENTS]=[{DOC_ID: x[DOC_ID], DOC_ATTRIBUTES: x[DOC_ATTRIBUTES]} for x in self._docs]
            data[DOCUMENTS] = [{DOC_ID: x[DOC_ID], DOC_ATTRIBUTES: x[DOC_ATTRIBUTES]} for x in self._docs]
         
        
        docs = self._docs
        attrs= self._attrs
        num_docs = len(docs)
        num_attrs = len(attrs)        
        
      
        # If we don't have any documents/attributes or we don't need to update, just return
        if num_docs == 0 or (not self._new_docs and not self._new_weights and not self._new_attrs) or num_attrs == 0:
            return
        #if less than 3 points selected for OLI => weights are not updated => return (as long as we don't need to add new docs/attrs)
        if not self._new_weights and not self._new_docs and not self._new_attrs:
            return
            
        # _vectorize transforms DOC_ATTRIBUTES into a matrix where each row
        # is a document and each column is an attribute
        self._new_docs = self._new_weights = False
        high_d, weight_list = self._vectorize(docs)
        attr_high_d , attr_weight_list  = self._attr_vectorize(attrs)
        
        # Pass the similarity weights down the pipeline
        #add similarity based on interaction => pass both of them 
        
        data["OBSERVATION"][SIMILARITY_WEIGHTS] = [{"id": x[0], "weight": x[1]} for x in weight_list]
        data[SIMILARITY_WEIGHTS] = [{"id": x[0], "weight": x[1]} for x in weight_list]
        data["ATTRIBUTE"][SIMILARITY_WEIGHTS] = [{"id": x[0], "weight": x[1]} for x in attr_weight_list]
        # We are updating now so make sure we only update again if we need to
        self._new_docs = self._new_weights = False
        """We need to run the forward MDS for both attribute and observation views when the user joins the room or when he resets """
        if (self._interaction == "none" or data ["prototype"] == 2):
          pdist = self._pairwise_distance(high_d, weight_list)
          attr_pdist = self._pairwise_distance( attr_high_d , attr_weight_list)
          if len(pdist) > 1:
            low_d = self._reduce(pdist, dimensions=self.low_dimensions)
          else:
            low_d = np.array([[0] * self.low_dimensions])
        
          low_d_max = low_d.max()
          low_d_min = low_d.min()
        
          if -low_d_min > low_d_max:
            low_d_max = -low_d_min
          if low_d_max == 0:
            low_d_max = 1
            
          if len(attr_pdist) > 1:
            attr_low_d = self._reduce(attr_pdist, dimensions=self.low_dimensions)
          else:
            attr_low_d = np.array([[0] * self.low_dimensions])
            
     
          attr_low_d_max = attr_low_d.max()
          attr_low_d_min = attr_low_d.min()
          if -attr_low_d_min > attr_low_d_max:
            attr_low_d_max = -attr_low_d_min
          if attr_low_d_max == 0:
            attr_low_d_max = 1
       
          # Set the low dimensional position of each document
          #change this also
          for i, pos in zip(range(len(data[DOCUMENTS])), low_d):
            doc = data[DOCUMENTS][i].copy()
            doc[LOWD_POSITION] = (pos / low_d_max).tolist()
           
             # Remember the high dimensional position of the point for inverse
            if DOC_ATTRIBUTES in doc:
                self._high_d[doc[DOC_ID]] = doc[DOC_ATTRIBUTES]
    
            
            data[DOCUMENTS][i] = doc
            data["OBSERVATION"][DOCUMENTS][i] =  doc
        
          
          for i, pos in zip(range(len(data["ATTRIBUTE"][ATTRIBUTE_LIST])), attr_low_d):
            attr = data["ATTRIBUTE"][ATTRIBUTE_LIST][i].copy()
            attr[LOWD_POSITION] = (pos / attr_low_d_max).tolist()  
            if ATTRIBUTE_DOCS in attr:
                self._attr_high_d [attr[ATTRIBUTE_ID]] = attr[ATTRIBUTE_DOCS]
    
            data["ATTRIBUTE"][ATTRIBUTE_LIST][i] = attr
            
        #call forward MDS  for OLI on observation view  or  move importance slider on attributes    
        elif self._view:
          pdist = self._pairwise_distance(high_d, weight_list)  
          if len(pdist) > 1:
            low_d = self._reduce(pdist, dimensions=self.low_dimensions)
          else:
            low_d = np.array([[0] * self.low_dimensions])
        
          low_d_max = low_d.max()
          low_d_min = low_d.min()
        
          if -low_d_min > low_d_max:
            low_d_max = -low_d_min
          if low_d_max == 0:
            low_d_max = 1
          
          for i, pos in zip(range(len(data[DOCUMENTS])), low_d):
            doc = data[DOCUMENTS][i].copy()
            doc[LOWD_POSITION] = (pos / low_d_max).tolist()
           
             # Remember the high dimensional position of the point for inverse
            if DOC_ATTRIBUTES in doc:
                self._high_d[doc[DOC_ID]] = doc[DOC_ATTRIBUTES]
    
            
            data[DOCUMENTS][i] = doc
            data["OBSERVATION"][DOCUMENTS][i] =  doc
        #call forward MDS  for OLI on attribute view  or  move importance slider on observation    
        elif self._view is False:
         
          attr_pdist = self._pairwise_distance( attr_high_d , attr_weight_list)   
          if len(attr_pdist) > 1:
            attr_low_d = self._reduce(attr_pdist, dimensions=self.low_dimensions)
          else:
            attr_low_d = np.array([[0] * self.low_dimensions])
            
     
          attr_low_d_max = attr_low_d.max()
          attr_low_d_min = attr_low_d.min()
          if -attr_low_d_min > attr_low_d_max:
            attr_low_d_max = -attr_low_d_min
          if attr_low_d_max == 0:
            attr_low_d_max = 1
          
          for i, pos in zip(range(len(data["ATTRIBUTE"][ATTRIBUTE_LIST])), attr_low_d):
            attr = data["ATTRIBUTE"][ATTRIBUTE_LIST][i].copy()
            attr[LOWD_POSITION] = (pos / attr_low_d_max).tolist()  
            if ATTRIBUTE_DOCS in attr:
                self._attr_high_d [attr[ATTRIBUTE_ID]] = attr[ATTRIBUTE_DOCS]
    
            
            data["ATTRIBUTE"][ATTRIBUTE_LIST][i] = attr
             
            
        data[INTERACTION]  = self._interaction
       
        
       
        
        
    def inverse(self, data):
        interaction = data[INTERACTION]
        self._interaction = data[INTERACTION]
        self._attrs_weights = pipeline.Model.global_attribute_weight_vector
        self._docs_weights = pipeline.Model.global_document_weight_vector
        self._weights = pipeline.Model.global_attribute_weight_vector

        if interaction == "change_relevance" or interaction =="none": 
            self._new_weights = True
        
        # If it's an OLI interaction, calculate a new set of weights based on
        # the selected set of points.
        if interaction == "oli":
      
            # data["points"] should be a dictionary containing the user-interacted
            # points, with the format
            # { DOC_ID: {
            #        "lowD": []
            #     },
            #    ...
            # }
            points = data["points"]
            self._view = data[VIEW]
             # An update on less than 3 points is meaningless
            if len(points) < 3:  
                
                return {}
            
            # Form the set of all attributes to form the matrix
            attributes = set()
            
            # Form the set of all attributes for observation view
            if self._view:
                attributes = set(self._weights.keys())
           
            #Form the set of all documents/attribute  for attribute view
            elif not self._view:
                attributes = set(self._docs_weights.keys())
                        
            attributes = list(attributes)
            high_d_matrix = np.zeros((len(points), len(attributes)), dtype=np.float64)
            
            keys = list(points.keys())
            
            # Fill in the highD matrix with the attribute values of the documents or document values of the attributes based on the used view (attrivute/observation)
            # Creates a vector format of our high dimensional data, but the input
            # is different than what _vectorize expects
            
            i = 0
            #change this to customized view
            for i in range(len(keys)): 
                for j in range(len(attributes)):
                    #observation view
                    if self._view:
                      if attributes[j] in self._high_d[keys[i]]:
                        high_d_matrix[i][j] = self._high_d[keys[i]][attributes[j]]
                    #attribute view
                    if self._view is False:
                      if attributes[j] in self._attr_high_d[keys[i]]:
                        high_d_matrix[i][j] = self._attr_high_d[keys[i]][attributes[j]]
            
            # Remove the dimensions with no variability
            high_d_matrix = np.array(high_d_matrix)
            num_dimensions = high_d_matrix.shape[1]
            keep_indeces = []
            for i in range(num_dimensions):
                if high_d_matrix[:,i].var() > 0:
                    keep_indeces.append(i)
                    
            for i in range(len(keys)):
                points[keys[i]]["highD"] = high_d_matrix[i][keep_indeces].tolist()
                
            high_dimensions = len(keep_indeces)
                
            request = {"points": points, 
                     "highDimensions": high_dimensions, 
                     "lowDimensions": self.low_dimensions,
                     "inverse": True,
                     "distanceFunc": self.dist_func
                     }
            request = json.dumps(request)
            request = request.encode(encoding='UTF-8')
            
            # Start the Java process
            # THIS IS WHERE INVERSE MDS HAPPENS. If you want to modify the inverse MDS
            # algorithm, either change this Java code or put a Python version here
            # instead.
            proc = subprocess.Popen(['java', '-jar', os.path.join(__location__, 'java/mds.jar')],
                                    stdin=subprocess.PIPE, 
                                    stdout=subprocess.PIPE)
            
            # Submit the json request, read the result, and set the weights
            output = proc.communicate(request)[0]
            output = json.loads(output)
            
            weights = np.zeros((num_dimensions))
            weights[keep_indeces] = output["weights"]
            
            # change weight vector based on used view
            if self._view :
               self._weights = {attributes[i]: weights[i] for i in range(num_dimensions)}
               pipeline.Model.global_attribute_weight_vector = self._weights
        
            elif self._view is False:
                self._docs_weights = {attributes[i]: weights[i] for i in range(num_dimensions)}
                pipeline.Model.global_document_weight_vector = self._docs_weights 
            
            self._new_weights = True
                
           
            return {} 
        
         
    def reset(self):
        self._weights = {}
        self._docs = []
        self._high_d = {}
        self._weights = {}
        self._attrs_weights = {}
        self._docs_weights = {}
        self._attrs = []
        self._attr_high_d ={}
        self._view = True
