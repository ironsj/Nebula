# -*- coding: utf-8 -*-
import copy
import math
import os
import re

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
#from nebula.pipeline import LOWD_POSITION
# The relevance of each document within the list
from nebula.pipeline import DOC_RELEVANCE
# A set of attribute names that exist in the data
from nebula.pipeline import ATTRIBUTES
# A dictionary of attribute weights
from nebula.pipeline import ATTRIBUTE_RELEVANCE
# A dictionary of attribute weight deltas from the most recent interaction
from nebula.pipeline import ATTRIBUTE_RELEVANCE_DELTA
# A list of weights for the similarity of attributes
#from nebula.pipeline import SIMILARITY_WEIGHTS
# An interaction, whose value is a string specifying the type of interaction
from nebula.pipeline import INTERACTION




class ActiveSetModel(pipeline.Model):
    """Maintains the active set of documents. The active set is the medium
    scale of data, in the range of thousands of documents. It's intent is to
    maintain a set of relevance weights for the attributes or high dimensional
    space. It then uses these weights to calculate a relevance for each
    document.
    
    While this is called the active set model, its output is the working set,
    which must be maintained as well. This is to ensure that the working set
    doesn't change drastically, only incrementally.
    
    For more thorough schema like representation, email phauck@vt.edu"""
    
    params = {"new_limit": "New doc limit",
              "working_limit": "Total working doc limit",
              "active_limit": "Total active doc limit",
              "search_increment": "Search weight increment",
              "modify_increment": "Modify weight increment",
              "delete_factor": "Delete weight increment"}
    
    def __init__(self, new_limit=5, working_limit=30, active_limit=10000,  search_increment=1, modify_increment=1, delete_factor=5):
        # The maximum number of new documents that can be added to the working 
        # set upon each interaction
        self.new_limit = new_limit
        
        # Maximum number of documents allowed in the working set
        self.working_limit = working_limit
          
        # Maximum number of documents allowed in the active set
        self.active_limit = active_limit
        
        # Delta that attribute weights are changed upon search interactions
        self.search_increment = search_increment
        
        # Delta that attribute weights are changed upon change relevance 
        # interactions
        self.modify_increment = modify_increment
        
        # Delta that attribute weights are decremented upon delete interactions
        # This decrement should be large enough to push the deleted document out
        # of the working set
        self.delete_factor = delete_factor
        
        # The Active Set contains all the documents that are currently candidate
        # for the working set
        self._active_set = {}
        
        # The Working Set is the set of documents currently being visualized
        self._working_set = {}
        
        # The set of relevancy weights over all attributes in the Active Set 
        # (distributed over pooled set, not per document)
        # Ex: If using TF-IDF, each term would be an attribute and have a weight
        # Ex: If using LDA, each topic would be an attribute and have a weight
        self._attr_weights = {}
        
        # A list of all attributes. This will be a superset of all keys in 
        # _attr_weights
        self._attributes = set()
        
    def forward_input_args(self): 
        return [DOC_ATTRIBUTES]
    
    def forward_output(self):
        return [DOC_RELEVANCE]
    
    def inverse_input_reqs(self):   
        return [INTERACTION]
    
    def inverse_output(self):
        return [ATTRIBUTE_RELEVANCE, ATTRIBUTE_RELEVANCE_DELTA]
    
    def setup(self, data):
        # Called upon startup or reset of the pipeline
        # Called at the pipeline level after the ActiveSetModel has been 
        # initialized
          
        if ATTRIBUTES in data:
            # Sets the initial list of attributes
            self._attributes.update(data[ATTRIBUTES])
       
        if DOCUMENTS in data:
            # Break out documents and their attributes into relevant sub-objects
            # of the ActiveSetModel
            #data[DOCUMENTS] all documents with their attr/weights and High dimesnsion position
            for doc in data[DOCUMENTS]:
                self._active_set[doc[DOC_ID]] = doc
            
                """I believe we don't need this for loop because all the attributes inside 
                documents are the same as those in  doc[ATTRIBUTES]"""
                for attr in doc[DOC_ATTRIBUTES]:
                   self._attributes.add(attr)
               
            # Prevent this data set from being accidentally accessed by Models
            # down the pipeline
            """ we don't want to pass any data to  simiarity model
             so  doc array inside simiarity model is not popluated and remains empty """
            del data[DOCUMENTS]
        
    def forward(self, data):
        self._attr_weights  =  pipeline.Model.global_weight_vector 
       
        if ATTRIBUTES in data:
            # Update the overall SET of attributes
            self._attributes.update(data[ATTRIBUTES])
          
        if DOCUMENTS in data:
            # We are receiving new documents to add to the active set
            # Calculate the relevance and see which we should add to
            # the working set
            for doc in data[DOCUMENTS]:
                self._active_set[doc[DOC_ID]] = doc
                for attr in doc[DOC_ATTRIBUTES]:
                    self._attributes.add(attr)
                         
            self._update_working_set(x[DOC_ID] for x in data[DOCUMENTS])
       
	
        # Calculate the relevance for each document in the working set.
        # Normalize it between 0 and 1 to simplify support for different
        # visualization clients.
        #max_relevance = 0
        for doc in self._working_set:
            relevance = self._relevance(self._working_set[doc])
            
            # Set the relevance for each working set document for the visualization
            self._working_set[doc][DOC_RELEVANCE] = relevance
            # Keep track of the maximum relevance of any document
            #if relevance > max_relevance:
             #   max_relevance = relevance
        """ 
        # Avoid divide by 0 error
        if max_relevance == 0:
            max_relevance = 1
   
        # Normalize the relevance of each document to be between 0 and 1
        for doc in self._working_set:
            self._working_set [doc][DOC_RELEVANCE] /= float(max_relevance)
        """         
        
        # Resets all the documents within the data blob as the current working
        # set
        data[DOCUMENTS] = list(self._working_set.values())
    
    def inverse(self, data):
        attr_weights_delta = {}
        interaction_attrs = {}
        weight_increase = False
        weight_decrease = False
        delta_diff = 0
        counter =0
        dec_relevance = False
        
        doc_matches = []
        oli_doc_matches = []
  
        self._attr_weights = pipeline.Model.global_weight_vector

        # Get the interaction type
        interaction = data[INTERACTION]      
       
        # Store the change in attribute weights that occur from this interaction 
        """ I can use it for storing the amount of increase but what about the slider movement ?? """
        if interaction == "search":
            # Get the search term entered by the user from the "query" key
            term = data["query"]

            if term != "":
                # Creates a regular expression for the search term
                prog = re.compile(term, flags=re.IGNORECASE)
                
                # Up-weights the attributes whose name matches the regular expression
                # for the search term.
                # Requires attribute names with meaning
                for attr in self._attributes:
                    if (attr.lower() == term.lower()):
                        weight_decrease = True
                        attr_weights_delta[attr] = 0.1
                    elif  prog.search(attr):  
                        weight_decrease = True
                        attr_weights_delta[attr] = 0.07

        elif interaction == "change_relevance":
            # Handles interactions where a document's relevance is changed
            # in the visualization

            # Get the user inputed new relevance value from the "relevance" key
            new_relevance =  float(data["relevance"])
           
            # Make sure the relevance is between 0 and 1
            #min value gives wrong results
            new_relevance = max(0.0, min(1.0, new_relevance))
            
            # Get the ID of the document whose relevance changed form the "id" key
            doc_id = data["id"]  
        
            # Make sure this document is in the working set
            if doc_id not in self._working_set:
                raise IndexError("Updated relevance for unknown document: %s" % doc_id)
            
            # Calculate the difference between the new and old relevance values
            old_relevance = self._working_set[doc_id][DOC_RELEVANCE]
            relevance_change = new_relevance - old_relevance

            sum_squares = 0
            for value in list(self._working_set[doc_id][DOC_ATTRIBUTES].values()):
                sum_squares +=  math.pow(value, 2) 

            if sum_squares != 0 and old_relevance != 0:
                for attr, value in self._working_set[doc_id][DOC_ATTRIBUTES].items():
                    if value != 0:  
                       attr_weights_delta[attr] =float( (value * ((new_relevance/old_relevance)-1)* old_relevance)/sum_squares )

                       # same as (new_relevance>old_relevance)
                       if (relevance_change > 0):
                            weight_decrease = True
                       else:
                            dec_relevance = True
                          #if(new_relevance == 0):
                           #    attr_weights_delta[attr]= -1*self._attr_weights[attr]
                          #else:
                            weight_increase = True
                            if (self._attr_weights[attr] + attr_weights_delta[attr]<0):  
                                attr_weights_delta[attr] = float (-1*self._attr_weights[attr])
                                
            else:
                return
                 
            # Update the relevance for the attributes in that document according
            # to the user defined change in the document's relevance
            # for attr, value in self._working_set[doc_id][DOC_ATTRIBUTES].iteritems():
            # attr_weights_delta[attr] = value * relevance_change * self.modify_increment

        elif interaction == "delete":
            # User selected delete document node
            doc_id = data["id"]

            # Defensive coding against a possible bug where a user selects
            # something not in the working set
            if doc_id not in self._working_set:
                raise IndexError("Deleting unknown document: %s" % doc_id)
           
            """ We  can use self.delete_factor = 0.5 but note that you have attr_weights_delta as dictonary between attr name(key) and value (increase/decrease) """
            # Down-weight the relevance for attributes in that document
            for attr, value in self._working_set[doc_id][DOC_ATTRIBUTES].items():
                if value != 0:
                    attr_weights_delta[attr] = value*-5
                    weight_increase = True
                    if (self._attr_weights[attr] + attr_weights_delta[attr] < 0):
                        attr_weights_delta[attr]= -1*self._attr_weights[attr]
                         
            # Remove the document from the working set
            del self._working_set[doc_id]
                
        interaction_attrs = dict(attr_weights_delta)
      
        #number of attributes to increase/decrease their weight based on  the interaction
        total_num_attr = len(self._attributes)-len(interaction_attrs)   
        #amount of weight to increase/decrease from other attributes
        weight_diff = float( sum(attr_weights_delta.values()))
       
        counter = 0
        count = 0
      
        zero_weight = True
        
        #In case of deleting node or decreasing the relevance, we should increase the weight of other terms
        if (weight_increase):
            weight_diff = -1* weight_diff
           
            for attr in self._attributes:   
                if attr not in interaction_attrs:
                    attr_weights_delta[attr] = ((weight_diff)/total_num_attr)
                    count += attr_weights_delta[attr]
             
        elif (weight_decrease): 
            while  (weight_diff > 0):
                zero_weight = True
                counter = 0  
                delta_diff =0  
                delta_dec = weight_diff/total_num_attr
               
                for attr in self._attributes:   
                    if attr not in interaction_attrs and attr in self._attr_weights:
                        if (attr_weights_delta.get(attr) is not None):  
                            if (attr_weights_delta[attr] + self._attr_weights[attr] ==0):
                                continue
                            elif (self._attr_weights[attr] + attr_weights_delta[attr]  - delta_dec) > 0:
                                attr_weights_delta[attr] += -1 * delta_dec
                                counter += 1
                            else:    
                                delta_diff +=  delta_dec - (self._attr_weights[attr]  + attr_weights_delta[attr])
                                attr_weights_delta[attr] =  -1 * self._attr_weights[attr]  
                            
                        else:  
                            if (self._attr_weights[attr] -  delta_dec) > 0:
                                attr_weights_delta[attr] = -1 *  delta_dec
                                counter += 1
                            else:
                                attr_weights_delta[attr] =  -1 * self._attr_weights[attr]
                                delta_diff += delta_dec - self._attr_weights[attr] 

                for attr in self._attributes:   
                    if attr not in interaction_attrs and attr in self._attr_weights: 
                        if (self._attr_weights[attr] + attr_weights_delta[attr] !=0):
                            zero_weight =False
               
                total_num_attr =  counter
                weight_diff =  delta_diff  
           
                delta_diff = 0  
                if(zero_weight):  
                    break         
                """ 
                if(counter ==0):
                    break
                """
           
            total_num_attr = len(interaction_attrs)     
            while(weight_diff > 0 and weight_decrease):
                delta_diff =0  
                counter=0
                delta_dec = weight_diff/total_num_attr 
                for inter_attr in  interaction_attrs: 
                    if(self._attr_weights[inter_attr] +attr_weights_delta[inter_attr] - delta_dec)>0 :
                        attr_weights_delta[inter_attr] -=  delta_dec
                        counter+=1
                    elif((self._attr_weights[inter_attr] +attr_weights_delta[inter_attr]) ==0):
                        continue
                    else:                        
                        delta_diff += delta_dec - (self._attr_weights[inter_attr] +attr_weights_delta[inter_attr])
                        attr_weights_delta[inter_attr] = - self._attr_weights[inter_attr]
                       
                total_num_attr =  counter
                weight_diff =  delta_diff  

        for attr in attr_weights_delta:
             if attr not in self._attr_weights:
                # Initialize it at 0
                self._attr_weights[attr] = 0

             self._attr_weights[attr] += attr_weights_delta[attr]

        print("Sum of wieghts after relevance update = %f"%sum(self._attr_weights.values()))

        pipeline.Model.global_weight_vector = self._attr_weights
        
        if(interaction == "delete" or dec_relevance ):
            return {}
             
        # Now that we have changed the weights based on the OLI interaction, check 
        # the relevance of each document in the active set to see whether it is a candidate to 
        # be added to the working set   
        if interaction == "oli":
            for doc_id in self._active_set:
                # Ignore any documents already in the working set
                if doc_id in self._working_set:
                    continue
                
                oli_interaction_relevance = 0
                
                oli_interaction_relevance = self._relevance(self._active_set[doc_id])
		
                if (oli_interaction_relevance > 0.1):
                    oli_doc_matches.append(doc_id)

        # Now that we have changed the weights based on the interaction, check 
        # each document in the active set to see whether it is a candidate to 
        # be added to the working set
        if len(attr_weights_delta) > 0:
            for doc_id in self._active_set:
                # Ignore any documents already in the working set
                if doc_id in self._working_set :    
                    continue
                
                interaction_relevance = 0
       
                # Iterate through each attribute in the document
                for attr, value in self._active_set[doc_id][DOC_ATTRIBUTES].items():
                    if attr in interaction_attrs: 
                        interaction_relevance += interaction_attrs[attr]*value
                            
                # If this document has a positive interaction relevance, add
                # it to the list of candidates to be added to the working set
                if interaction_relevance > 0:             
                    doc_matches.append(doc_id)

        """ This means that if I only find one document in active set, 
        i will not pull any data from data controller  """ 
       
        if len(doc_matches) > 0:
            # We have new candidates, so update the working set
            if (interaction == "search" ):
                self._update_working_set(doc_matches,10)
            else:
                self._update_working_set(doc_matches)  

            return {}
                
        elif len(oli_doc_matches) > 0:
            self._update_working_set(oli_doc_matches)
            
            return {}
        
        else:
            # We had no matches in the active set, so request more documents
            # from upstream.
            # This is the mechanism by which a data controller or document store
            # model can add to documents in the active set
            """ I have commented this code because in the current implementation 
            the active set is the same as the document set so we don't need to pull new documents
            it will be  a redundant process """
            """if len(attr_weights_delta) > 0 :
                # Let upstream models know about the updated weights
                data[ATTRIBUTE_RELEVANCE] = copy.copy(self._attr_weights)
                data[ATTRIBUTE_RELEVANCE_DELTA] = copy.copy(attr_weights_delta)
            """
            return {}
            # Otherwise, either the search didn't match any attributes
            # or we haven't loaded any attributes from up stream, so pass
            # the search on, leaving the interaction in place
           
    def _relevance(self, doc):
        # Calculate the relevance score for a single document
        relevance = 0
       
        for attr, value in doc[DOC_ATTRIBUTES].items():     
            if attr in self._attr_weights:         
                # Add relevance for each attribute to get total relevance
               relevance += self._attr_weights[attr] * value
               
        return relevance
    
    def _update_working_set(self, candidates, max_limit = 0):
        # candidates: a list of document IDs
        # Calculate the relevance for each candidate
        new_relevances = []
        
        for doc_id in candidates:
            # For each document ID in candidates, calculate its relevance to
            # the active set. Keep relevances in a list.
            relevance = self._relevance(self._active_set[doc_id])
            new_relevances.append((doc_id, relevance))
       
        # Sort the newly calculated relevances in descending order to select
        # the most relevant documents to add to the working set
        new_relevances = sorted(new_relevances, key=lambda x: x[1], reverse=True)
        
        # Limit the number of new documents that will be added to the working
        # set to user defined limit
        limit = len(new_relevances)
        if(max_limit!=0):
            if max_limit < limit:
                limit = max_limit 
        else:   
            if self.new_limit < limit:
               limit = self.new_limit
                 
        # First remove documents if we will exceed the total working set limit
        removal = len(self._working_set) + limit - self.working_limit
        if removal > 0:
            # Calculate the relevance of all documents in the working set
            current_relevances = []
            for doc_id in self._working_set:
                relevance = self._relevance(self._working_set[doc_id])
                current_relevances.append((doc_id, relevance))
                
            current_relevances = sorted(current_relevances, key=lambda x: x[1])
        
            # Remove the least relevant documents to make space for new documents
            for i in range(removal):
                doc_id = current_relevances[i][0]
                del self._working_set[doc_id] 
        
        # Now add the most relevant candidates to the working set
        # Limit ourselves to a user defined number of new documents
        for i in range(limit):
            doc_id = new_relevances[i][0]
            self._working_set[doc_id] = self._active_set[doc_id]
        
    def reset(self):
        self._active_set = {}
        self._working_set = {}
        self._attr_weights = {}
