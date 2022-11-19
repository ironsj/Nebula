# -*- coding: utf-8 -*-
import os
import re
import numpy as np
import sys

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

#from nebula.pipeline import VIEW
from nebula.pipeline import ATTRIBUTE_LIST
#from nebula.pipeline import DOCUMENTS_LIST
from nebula.pipeline import ATTRIBUTE_ID
from nebula.pipeline import ATTRIBUTE_DOCS



class ImportanceModel(pipeline.Model):
    """Maintains the  set of documents and attributes for both views. The active_set is the set of all documents/attributes. 
    It's intent is to maintain weights for the attributes/documents or high dimensional
    space. It then uses these weights to calculate a relevance for each document/attrbute. """
    
    def __init__(self, should_query=False, new_limit=5, working_limit=30, active_limit=10000,  search_increment=1, modify_increment=1, delete_factor=5):
        # Determine whether this Model should even query or if it should just
        # display all the data
        self._should_query = should_query

        # The maximum number of new documents that can be added to the working 
        # set upon each interaction
        self.new_limit = new_limit
        
        # Dynamically set the transitive new limit
        self.transitive_new_limit = self.new_limit // 2
        
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


        # The doc_active Set contains all the documents 
        self._doc_active_set = {}
        
        # The attr_active Set contains all the attributes
        self._attr_active_set = {}

        # The Working Set is the set of documents currently being visualized
        self._doc_working_set = {}

        # The Working Set is the set of attributes currently being visualized
        self._attr_working_set = {}
        
        #maintains the interaction 
        self._interaction = ""
        #keep track of which view is used to use appropriate weight vector
        self._view = True
        
        #which prototype to run
        self._prototype = 0
        
        # weight vectors for documents/attributes
        self._attrs_weights = {}
        self._docs_weights = {}
        self._weights = {}

        # A list of all attributes. This will be a superset of all keys in 
        # _attr_weights
        self._attributes = set()

        # A list of all documents. This will be a superset of all keys in 
        # _docs_weights
        self._docs = set()

        # A set of documents that were added in the inverse step
        self._newly_added_docs = {}

        # A set of attributes that were added in the inverse step
        self._newly_added_attrs = {}
        
        # A set of flags to track whether an interaction occurred in the doc
        # panel or attr panel
        self._doc_interaction = False
        self._attr_interaction = False
        
        # A set of flags to track how the views should communicate with each
        # other after each interaction
        self._doc_feedback = True
        self._attr_feedback = True
        
        # A set of flags to track whether querying should occur for either
        # the documents or the attributes
        self._doc_forage = should_query
        self._attr_forage = should_query
        
        # A flag to determine when auto foraging should occur after an
        # increase in relevance value
        self._should_auto_forage_for_relevance_change = False
       
    #need to modify these to fit the model ****TODO    
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
        pass
        
#        if  ATTRIBUTE_LIST in data:
#            for attr in data[ATTRIBUTE_LIST]:
#                self._attr_active_set [attr[ATTRIBUTE_ID]] = attr
#            
#            del data[ATTRIBUTE_LIST]
#        
#        if DOCUMENTS in data:
#            for doc in data[DOCUMENTS]:
#                self._doc_active_set [doc[DOC_ID]] = doc
#            del data[DOCUMENTS]
        

        if ATTRIBUTES in data:
            # Sets the initial list of attributes
            self._attributes.update(data[ATTRIBUTES])
       
        if DOCUMENTS in data:
            # Break out documents and their attributes into relevant sub-objects
            # of the ActiveSetModel
            #data[DOCUMENTS] all documents with their attr/weights and High dimesnsion position
            for doc in data[DOCUMENTS]:
                self._doc_active_set[doc[DOC_ID]] = doc
            
                """I believe we don't need this for loop because all the attributes inside 
                documents are the same as those in  doc[ATTRIBUTES]"""
                for attr in doc[DOC_ATTRIBUTES]:
                   self._attributes.add(attr)


        if DOCUMENTS in data:
            # Sets the initial list of documents
            self._docs.update(data[ATTRIBUTES])
       
        if ATTRIBUTE_LIST in data:
            # Break out attributes and their documents into relevant sub-objects
            # of the ActiveSetModel
            #data[ATTRIBUTES] all attributes with their docs/weights and High dimesnsion position
            for attr in data[ATTRIBUTE_LIST]:

                self._attr_active_set[attr[ATTRIBUTE_ID]] = attr
            
                """I believe we don't need this for loop because all the attributes inside 
                documents are the same as those in  doc[ATTRIBUTES]"""
                for doc in attr[ATTRIBUTE_DOCS]:
                   self._docs.add(doc)


        # Prevent this data set from being accidentally accessed by Models
        # down the pipeline
        """ we don't want to pass any data to  simiarity model
        so  doc array inside simiarity model is not popluated and remains empty """
        del data[DOCUMENTS]
        del data[ATTRIBUTE_LIST]

        # If we're not querying the data, go ahead and add everything to the
        # working set so that all of it is displayed at once
        if not self._should_query:
            self._attr_working_set = self._attr_active_set
            self._doc_working_set = self._doc_active_set
        
    # Method to update the specified weight vector after a given term/item has
    # had its relevance/importance updated (via the slider in the UI)
    def update_weights(self, weights, relevance, term):
        weights_deltas = {}
        weight_change = relevance - weights[term]
        if relevance > weights[term]:
           weights_deltas[term] = weight_change
           weights[term] += weight_change 
           init_counter = 0
           for doc_weight in weights:
                if doc_weight != term:
                    if weights[doc_weight] != 0:    
                        init_counter += 1
           total_num = init_counter
           old_weight_change = weight_change
           old_counter = total_num
           while weight_change > 0 and total_num > 0:
                delta_dec = weight_change / total_num
                counter = 0 
                for doc_weight in weights:   
                    if doc_weight != term:
                         if weights[doc_weight] == 0:
                            continue;
                         elif (weights[doc_weight] - delta_dec) >= 0:
                            weights[doc_weight] -= delta_dec
                            counter += 1
                            weight_change -= delta_dec
                         elif (weights[doc_weight] - delta_dec) < 0:
                            weight_change -= weights[doc_weight]
                            weights[doc_weight] = 0
                            
                total_num = counter
                
                if old_weight_change == weight_change and weight_change <= sys.float_info.epsilon:
                    break
                else:
                    old_weight_change = weight_change
        
        else:
            total_num = len(weights) - 1 
            weights[term] += weight_change
            #weights_deltas[term] = weight_change
            delta_dec = (-1* weight_change) / total_num
            for weight in weights:
               if weight != term:
                  weights[weight] += delta_dec
                  #weights_deltas[weight] = delta_dec
                  
        return weights_deltas
    
    # Helper function to update the relevance of all documents or all attributes
    def update_weights_relevance(self, working_set, flag):
        item_relevance = {}
        for item in working_set:
            item_relevance[item] = self._relevance(working_set[item], flag)

        return item_relevance  
        
        
    """For all the weights that we are using, we need to scale them
    to sum to 1, but we don't want to squash the weights that
    best describe the layout too much. By taking every weight to
    a certain power, we emphasize the large weights while keeping
    the small weights small. By using an exponent that is a function
    of the number of weights, we let the weights scale to appropriately
    account for the fact that a larger number of weights will try
    to squash our weights even more """
    def _rescale_weights(self, weights):
        # First check that we have weights to manipulate
        if len(weights) > 0:
        
            # Emphasize large weights
            for item in  weights:
                weights[item] = weights[item] ** ((len(weights)/7.0))

            # Shift values up if we have a negative min weight
            min = np.min(list(weights.values()))
            if (min < 0):
                for item in weights:
                    weights[item] += min

            # Ensure weights sum to 1
            sum = np.sum(list(weights.values()))
            for item in  weights:
                weights[item] /= sum
        
        return weights
       
              
    def forward(self, data):

        if ATTRIBUTES in data:
            # Update the overall SET of attributes
            self._attributes.update(data[ATTRIBUTES])
          
        if DOCUMENTS in data:
            # We are receiving new documents to add to the active set
            # Calculate the relevance and see which we should add to
            # the working set
            for doc in data[DOCUMENTS]:
                self._doc_active_set[doc[DOC_ID]] = doc
                for attr in doc[DOC_ATTRIBUTES]:
                    self._attributes.add(attr)

        if DOCUMENTS in data:
            # Update the overall SET of attributes
            self._docs.update(data[ATTRIBUTES])
          
        if ATTRIBUTE_LIST in data:
            # We are receiving new documents to add to the active set
            # Calculate the relevance and see which we should add to
            # the working set
            for attr in data[ATTRIBUTE_LIST]:
                self._attr_active_set[attr[ATTRIBUTE_ID]] = attr
                for doc in attr[ATTRIBUTE_DOCS]:
                    self._docs.add(attr)


        if self._prototype == 2:
          if self._interaction == "none":
            
            attr_weights = {}
            doc_weights = {}
            attr_weights = self.update_weights_relevance(self._attr_working_set, False)              
            doc_weights = self.update_weights_relevance(self._doc_working_set, True)
            self._weights = self._rescale_weights(attr_weights)
            self._docs_weights = self._rescale_weights(doc_weights)
           
          elif self._interaction == "oli":
              if self._view and self._doc_feedback:
                self._docs_weights = self.update_weights_relevance(self._doc_working_set, True)
                self._docs_weights = self._rescale_weights(self._docs_weights)       
                #or
                #self._docs_weights = self._rescale_weights(self.update_weights_relevance(self._doc_active_set,True))

              elif (not self._view) and self._attr_feedback:
                self._weights = self.update_weights_relevance(self._attr_working_set, False)
                self._weights = self._rescale_weights(self._weights) 
                #or
                #self._weights = self._rescale_weights(self.update_weights_relevance(self._attr_active_set,False))
                
          elif self._interaction == "change_relevance":
              
              # Update the relevance of the correct weight vector
              if self._doc_interaction and self._doc_feedback:
                  self._weights = self.update_weights_relevance(self._attr_working_set, False)
                  self._weights = self._rescale_weights(self._weights)
                  
                  self._docs_weights = self.update_weights_relevance(self._doc_working_set, True)
                  self._docs_weights = self._rescale_weights(self._docs_weights)
              elif self._attr_interaction and self._attr_feedback:
                  self._docs_weights = self.update_weights_relevance(self._doc_working_set, True)
                  self._docs_weights = self._rescale_weights(self._docs_weights)
                  
                  self._weights = self.update_weights_relevance(self._attr_working_set, False)
                  self._weights = self._rescale_weights(self._weights)
          
          
          # Do a "transitive" search
          if self._interaction != "none" and self._should_query:
            should_transitive_search_docs = self._newly_added_attrs and self._doc_interaction and self._should_auto_forage(shouldForageOnSearch=self._doc_forage, isSearchingForDocs=True)
            should_transitive_search_attrs = self._newly_added_docs and self._attr_interaction and self._should_auto_forage(shouldForageOnSearch=self._attr_forage, isSearchingForDocs=False)
            
            # Store the values for the newly added documents/attributes in
            # case we are doing a transitive search on both (e.g., a search
            # returned both documents and attributes)
            newly_added_docs = self._newly_added_docs
            newly_added_attrs = self._newly_added_attrs
            
            # Transitive search for documents
            if should_transitive_search_docs:
                self._automated_foraging(None, newly_added_attrs, True, True)
                if len(self._newly_added_docs) > 0:
                    for doc in self._newly_added_docs:
                        self._docs_weights[doc] = self._relevance(self._doc_working_set[doc], True)
                    self._docs_weights = self._rescale_weights(self._docs_weights)
                    
            # Transitive search for attributes
            if should_transitive_search_attrs:
                self._automated_foraging(None, newly_added_docs, False, True)
                if len(self._newly_added_attrs) > 0:
                    for attr in self._newly_added_attrs:
                        self._weights[attr] = self._relevance(self._attr_working_set[attr], False)
                    self._weights = self._rescale_weights(self._weights)

          print("Sum of attr weights after forward = %f" % sum(self._weights.values()))
          print("Sum of doc weights after forward = %f" % sum(self._docs_weights.values()))
          pipeline.Model.global_document_weight_vector = self._docs_weights 
          pipeline.Model.global_attribute_weight_vector = self._weights

        if DOCUMENTS in data:
            self._update_working_set((x[DOC_ID] for x in data[DOCUMENTS]), True)


        if ATTRIBUTE_LIST in data:
            self._update_working_set((x[ATTRIBUTE_ID] for x in data[ATTRIBUTE_LIST]), False)
       
	
        data[DOCUMENTS] = list(self._doc_working_set.values())
        data[ATTRIBUTE_LIST] = list(self._attr_working_set.values())

        # These are what the previous 2 lines used to be in the original SIRIUS
        # Can probably delete these... I don't think they're necessary anymore
        #data[DOCUMENTS] = self._doc_active_set.values()
        #data[ATTRIBUTE_LIST] = self._attr_active_set.values()
        
        data["prototype"] = self._prototype
        if (self._interaction != "none"):
             data["view"] = self._view
           
        
    def inverse(self, data):
       
        self._interaction = data[INTERACTION]
        self._prototype = data["prototype"]

        # Separate the documents from the attributes; they are both in self._docs
        doc_list = []
        for doc in self._docs:
            if doc not in self._attributes:
                doc_list.append(doc)
        

        # Set things up to track changes that need to be made to the weight vectors
        # I don't think many of these variables are necessary anymore
        attr_weight_decrease = False
        attr_weight_increase = False
        doc_weight_decrease = False
        doc_weight_increase = False
        attr_weights_delta = {}
        doc_weights_delta = {}
        # I don't think this variable is necessary anymore
        dec_relevance = False
        
        # Set flags to track whether docs or attributes are being interacted with
        self._doc_interaction = False
        self._attr_interaction = False
        
        # Set flags to track whether docs or attributes should be foraged
        # Capture flags for whether to allow foraging between views
        if "docForage" in data:
            self._doc_forage = data["docForage"]
        if "attrForage" in data:
            self._attr_forage = data["attrForage"]

        if self._interaction == "search":

            # Get the search term entered by the user from the "query" key
            term = data["query"]

            if term != "":

                # Up-weights the attributes whose name matches the regular expression
                # for the search term.
                # Requires attribute names with meaning
                attr_weights_delta, attr_weight_increase, attr_weight_decrease, self._attr_interaction = self._search_for_term(term, self._attributes, isObservation=False)

                # Up-weights the documents whose name matches the regular expression
                # for the search term.
                # Requires document names with meaning
                doc_weights_delta, doc_weight_increase, doc_weight_decrease, self._doc_interaction = self._search_for_term(term, doc_list, isObservation=True)
       
        else:
            
            if (self._interaction != "none"):
                
               # Capture which "view" is being interacted with
               self._view  = data["view"]
               
               # Capture flags for whether to allow feedback between views
               self._doc_feedback = data["docFeedback"]
               self._attr_feedback = data["attrFeedback"]


            self._docs_weights = pipeline.Model.global_document_weight_vector
            self._weights = pipeline.Model.global_attribute_weight_vector



            if self._interaction == "change_relevance": 
              new_relevance =  float(data["relevance"])

              #Observation view
              if (self._view):
                     if(self._prototype == 1):
                       self._view = False
                     doc_weights_delta = self.update_weights(self._docs_weights, new_relevance, data["id"])
                     pipeline.Model.global_document_weight_vector = self._docs_weights
                     self._doc_interaction = True
                     
                     # Only permit auto foraging if we increased an item's
                     # relevance, as denoted by doc_weights_delta having data
                     if not doc_weights_delta:
                         self._should_auto_forage_for_relevance_change = False
                     else:
                         self._should_auto_forage_for_relevance_change = True
                     
              #attribute view                
              elif (not self._view):
                     if(self._prototype == 1):
                        self._view = True
                     attr_weights_delta = self.update_weights(self._weights, new_relevance, data["id"])
                     pipeline.Model.global_attribute_weight_vector = self._weights
                     self._attr_interaction = True
                     
                     # Only permit auto foraging if we increased an item's
                     # relevance, as denoted by attr_weights_delta having data
                     if not attr_weights_delta:
                         self._should_auto_forage_for_relevance_change = False
                     else:
                         self._should_auto_forage_for_relevance_change = True
                     
                     
                     
            if self._interaction == "oli":
                if self._view:
                    self._doc_interaction = True
                    for doc in data["points"]:
                        doc_weights_delta[doc] = self._docs_weights[doc]
                else:
                    self._attr_interaction = True
                    for attr in data["points"]:
                        attr_weights_delta[attr] = self._weights[attr]


        if(self._interaction == "delete"):
            # User selected delete document node
            data_id = data["id"]

            # Defensive coding against a possible bug where a user selects
            # something not in the working set
            if data_id not in self._doc_working_set and data_id not in self._attr_working_set:
                raise IndexError("Deleting unknown item: %s" % data_id)
           
            """ We  can use self.delete_factor = 0.5 but note that you have attr_weights_delta as dictonary between attr name(key) and value (increase/decrease) """
            # Down-weight the relevance for attributes in that document
            if data_id in self._doc_working_set:
                self._doc_interaction = True
                for attr, value in self._doc_working_set[data_id][DOC_ATTRIBUTES].items():
                    if value != 0 and attr in self._attr_working_set:
                        attr_weights_delta[attr] = value * -5
                        attr_weight_increase = True
                        if (self._weights[attr] + attr_weights_delta[attr] < 0):
                            attr_weights_delta[attr]= -1 * self._weights[attr]
                         
                # Remove the document from the working set and the weight vector
                del self._doc_working_set[data_id]
                del self._docs_weights[data_id]
                
            """ We  can use self.delete_factor = 0.5 but note that you have attr_weights_delta as dictonary between attr name(key) and value (increase/decrease) """
            # Down-weight the relevance for documents in that attribute
            if data_id in self._attr_working_set:
                self._attr_interaction = True
                for doc, value in self._attr_working_set[data_id][ATTRIBUTE_DOCS].items():
                    if value != 0 and doc in self._doc_working_set:
                        doc_weights_delta[doc] = value * -5
                        doc_weight_increase = True
                        if (self._docs_weights[doc] + doc_weights_delta[doc] < 0):
                            doc_weights_delta[doc]= -1 * self._docs_weights[doc]
                         
                # Remove the attribute from the working set and the weight vector
                del self._attr_working_set[data_id]
                del self._weights[data_id]
                
                
                
        interaction_attrs = dict(attr_weights_delta)
        interaction_docs = dict(doc_weights_delta)
      
        # I don't think any of these variables are ncessary anymore...
        #number of attributes to increase/decrease their weight based on  the interaction
        total_num_attr = len(self._attributes)-len(interaction_attrs)   
        #amount of weight to increase/decrease from other attributes
        attr_weight_diff = float(sum(attr_weights_delta.values()))
        #number of documents to increase/decrease their weight based on  the interaction
        total_num_docs = len(self._docs) - len(self._attributes) - len(interaction_docs)   
        #amount of weight to increase/decrease from other attributes
        doc_weight_diff = float(sum(doc_weights_delta.values()))

        # Rescale the weights if necessary. This is only used when we have
        # foraged for new items. At this point, this should only be possible
        # if we have searched for a term
        if self._should_query and (self._interaction == "search" or self._interaction == "delete") and self._attr_interaction:
            self._compensate_weight_changes(attr_weights_delta, interaction_attrs, self._attributes, self._weights, total_num_attr, attr_weight_increase, attr_weight_decrease)
            self._rescale_weights(self._weights)
        if self._should_query and (self._interaction == "search" or self._interaction == "delete") and self._doc_interaction:
            self._compensate_weight_changes(doc_weights_delta, interaction_docs, doc_list, self._docs_weights, total_num_docs, doc_weight_increase, doc_weight_decrease)
            self._rescale_weights(self._docs_weights)


        # Automated foraging for documents
        if self._attr_interaction and self._should_auto_forage(shouldForageOnSearch=True, isSearchingForDocs=True) and len(doc_weights_delta) < self.new_limit:

            # If we did an attribute interaction, automatically search for new
            # documents
            self._automated_foraging(attr_weights_delta, interaction_attrs, isSearchingForDocs=True)
            
            # Update the weight vector to account for the new documents
            if len(self._newly_added_docs) > 0:
                for doc_id in self._doc_working_set:
                    self._docs_weights[doc_id] = self._relevance(self._doc_working_set[doc_id], True)
                total_docs_added = set(list(doc_weights_delta.keys()) + list(self._newly_added_docs.keys())) & set(self._attr_working_set.keys())
                if len(total_docs_added) > self.new_limit:
                    chosen_items = sorted(total_docs_added, reverse=True)[:self.new_limit]
                    for doc in total_docs_added:
                        if doc not in chosen_items:
                            if doc in self._docs_weights:
                                del self._docs_weights[doc]
                            if doc in self._doc_working_set:
                                del self._doc_working_set[doc]
                self._docs_weights = self._rescale_weights(self._docs_weights)
                
        # If we're going to forage for new attrs later, use the entire document
        # working set to do the forage
        elif self._should_query and self._attr_forage:
            self._newly_added_docs = self._doc_working_set
        
        # If we're not doing any automated foraging for docs, ensure the list
        # of newly added docs is empty
        else:
            self._newly_added_docs = {}
            
            
        # Atomated foraging for attributes
        if self._doc_interaction and self._should_auto_forage(shouldForageOnSearch=True, isSearchingForDocs=False) and len(attr_weights_delta) < self.new_limit:
            
            # First, save the current state of _newly_added_docs in case we don't
            # change this set later; _automated_foraging will rewrite it
            saved_newly_added_docs = self._newly_added_docs
            
            # If we did a document interaction, automatically search for new
            # attributes
            self._automated_foraging(doc_weights_delta, interaction_docs, isSearchingForDocs=False)
            
            # Update the weight vector to account for the new attributes
            if len(self._newly_added_attrs) > 0:
                total_attrs_added = set(list(attr_weights_delta.keys()) + list(self._newly_added_attrs.keys())) & set(self._attr_working_set.keys())
                for attr_id in self._attr_working_set:
                    self._weights[attr_id] = self._relevance(self._attr_working_set[attr_id], False)
                if len(total_attrs_added) > self.new_limit:
                    chosen_items = sorted(total_attrs_added, reverse=True)[:self.new_limit]
                    for attr in total_attrs_added:
                        if attr not in chosen_items:
                            if attr in self._weights:
                                del self._weights[attr]
                            if attr in self._attr_working_set:
                                del self._attr_working_set[attr]
                self._weights = self._rescale_weights(self._weights)
            
            # _newly_added_docs has been rewritten. If its length is 0, then
            # we should try using the saved set instead
            if len(self._newly_added_docs) == 0:
                self._newly_added_docs = saved_newly_added_docs
                
                
        # If we're going to forage for new docs later, use the entire attribute
        # working set to do the forage
        elif self._should_query and self._doc_forage:
            self._newly_added_attrs = self._attr_working_set
        
        # If we're not doing any automated foraging for attrs, ensure the list
        # of newly added attrs is empty
        else:
            self._newly_added_attrs = {}
            
            
        print("Sum of attr weights after inverse = %f" % sum(self._weights.values()))
        print("Sum of doc weights after inverse = %f" % sum(self._docs_weights.values()))
        pipeline.Model.global_attribute_weight_vector = self._weights
        pipeline.Model.global_document_weight_vector = self._docs_weights
        
        return {} 
                 
    # Calculate the relevance score for a single document or attribute
    def _relevance(self, item, view):
        
        relevance = 0

        if(view):
          for attr, value in item[DOC_ATTRIBUTES].items():
           if attr in self._weights:      
              # Add relevance for each attribute to get total relevance
              relevance += self._weights[attr] * value 
          
        else:
          for doc, value in item[ATTRIBUTE_DOCS].items():
           if doc in self._docs_weights:
                relevance += self._docs_weights[doc] * value              
        
        return relevance

    def _search_for_term(self, term, data_list, isObservation):
        
        # Determine which working set and active set to use
        working_set = {}
        active_set = {}
        if isObservation:
            working_set = self._doc_working_set
            active_set = self._doc_active_set
        else:
            working_set = self._attr_working_set
            active_set = self._attr_active_set

        # Set up return variables, which are used to compensate for weight
        # changes
        weight_increase = False
        weight_decrease = False
        weights_delta = {}
        new_items_found = False
        
        # Initialize object to contain all matched entities
        matched_items = {}

        # Creates a regular expression for the search term
        prog = re.compile(term, flags=re.IGNORECASE)

        # Up-weights the attributes whose name matches the regular expression
        # for the search term.
        # Requires attribute names with meaning
        for item in data_list:
            if (item.lower() == term.lower()):
                if item not in working_set:
                    weight_decrease = True
                    weights_delta[item] = 0.1
                    matched_items[item] = active_set[item]
                    new_items_found = True

            elif  prog.search(item):
                if item not in working_set:
                    weight_decrease = True
                    weights_delta[item] = 0.07
                    matched_items[item] = active_set[item]
                    new_items_found = True
                    
        # Based on the number of matched items and their relevances, determine
        # which should be added to the working set
        self._update_working_set(matched_items, view=isObservation)
        
        for item in (set(weights_delta.keys()) - set(working_set.keys())):
            del weights_delta[item]
            
        # If there are no items left in weights_delta, then set the flags to
        # False
        if len(list(weights_delta.keys())) == 0:
            weight_increase = False
            weight_decrease = False
            new_items_found = False
            
        # weights_increase is not used, so we only have to check if the sum of
        # all the weights_delta is <= 0 to see if weight_decrease should be
        # reset
        elif sum(weights_delta.values()) <= 0:
            weight_decrease = False
        

        return weights_delta, weight_increase, weight_decrease, new_items_found


    def _compensate_weight_changes(self, weights_delta, interaction_list, data_list, weights, total_num_items, weight_increase, weight_decrease):
        #amount of weight to increase/decrease from other attributes
        weight_diff = float(sum(weights_delta.values()))
       
        counter = 0
        count = 0
              
        #In case of deleting node or decreasing the relevance, we should increase the weight of other terms
        if weight_increase:
            weight_diff = -1* weight_diff
           
            for item in data_list:   
                if item not in interaction_list:
                    weights_delta[item] = ((weight_diff)/total_num_items)
                    count += weights_delta[item]
             
        elif weight_decrease:
            while  (weight_diff > 0):
                zero_weight = True
                counter = 0  
                delta_diff = 0
                delta_dec = weight_diff/total_num_items
               
                for item in data_list:
                    if item not in interaction_list and item in weights:
                        if (weights_delta.get(item) is not None):
                            if (weights_delta[item] + weights[item] == 0):
                                continue
                            elif (weights[item] + weights_delta[item] - delta_dec) > 0:
                                weights_delta[item] += -1 * delta_dec
                                counter += 1
                            else:    
                                delta_diff +=  delta_dec - (weights[item] + weights_delta[item])
                                weights_delta[item] = -1 * weights[item]  
                            
                        else:
                            if (weights[item] -  delta_dec) > 0:
                                weights_delta[item] = -1 *  delta_dec
                                counter += 1
                            else:
                                weights_delta[item] =  -1 * weights[item]
                                delta_diff += delta_dec - weights[item] 

                for item in data_list:
                    if item not in interaction_list and item in weights: 
                        if (weights[item] + weights_delta[item] !=0):
                            zero_weight = False
               
                total_num_items = counter
                weight_diff = delta_diff  
           
                delta_diff = 0  
                if(zero_weight):  
                    break         
                """ 
                if(counter ==0):
                    break
                """
           
            total_num_items = len(interaction_list)     
            while(weight_diff > 0 and weight_decrease):
                delta_diff = 0  
                counter = 0
                delta_dec = weight_diff/total_num_items
                for inter_item in interaction_list: 
                    if(weights[inter_item] + weights_delta[inter_item] - delta_dec) > 0:
                        weights_delta[inter_item] -= delta_dec
                        counter+=1
                    elif((weights[inter_item] + weights_delta[inter_item]) == 0):
                        continue
                    else:
                        delta_diff += delta_dec - (weights[inter_item] + weights_delta[inter_item])
                        weights_delta[inter_item] = -weights[inter_item]
                       
                total_num_items =  counter
                weight_diff =  delta_diff

                delta_diff = 0  
                if(zero_weight):  
                    break         
                """ 
                if(counter ==0):
                    break
                """

        for item in weights_delta:
             if item not in weights:
                # Initialize it at 0
                weights[item] = 0

             weights[item] += weights_delta[item]
             
    # Helper function to determine when automated foraging should occur
    def _should_auto_forage(self, shouldForageOnSearch, isSearchingForDocs):
        interactions_w_no_foraging = self._interaction == "delete"
        interactions_must_forage = self._interaction == "search" and shouldForageOnSearch
        interactions_may_forage = self._interaction == "oli" or (self._interaction == "change_relevance" and self._should_auto_forage_for_relevance_change)
        if isSearchingForDocs:
            return self._should_query and not interactions_w_no_foraging and (interactions_must_forage or (self._doc_forage and interactions_may_forage))
        else:
            return self._should_query and not interactions_w_no_foraging and (interactions_must_forage or (self._attr_forage and interactions_may_forage))

    # Function to perform automated foraging for additional data to display based
    # on the changes in weights
    def _automated_foraging(self, weights_delta, interaction_list, isSearchingForDocs, isTransitiveSearch=False):

        # Initialize arrays of potential candidates to add to the working set
        item_matches = []
        oli_item_matches = []

        # Determine the appropriate working set and active set to use
        active_set = {}
        working_set = {}
        if isSearchingForDocs:
            active_set = self._doc_active_set
            working_set = self._doc_working_set
        else:
            active_set = self._attr_active_set
            working_set = self._attr_working_set
            
        # Set a relevance threshold to be a twentieth of the average weight for
        # the working set. This should be big enough to not add any items
        # that are not "relevant enough," but not so high that we throw
        # away potentially relevant results
        # By default, this value will be set to a twentieth of the average
        # weight for the default number of items that will be added to the
        # working set (which is self.new_limit)
        relevance_threshold = (1.0/self.new_limit) / 20
        if len(working_set) > 0:
            relevance_threshold = (1.0/len(working_set))/20

        # Now that we have changed the (e.g., attribute) weights based on the OLI interaction, check 
        # the relevance of each item (e.g., document) in the active set to see whether it is a candidate to 
        # be added to the working set   
        if self._interaction == "oli":

            for item_id in active_set:
                
                # Ignore any documents already in the working set
                if item_id in working_set:
                    continue
                                
                # If the relevance of the given item is greater than the
                # relevance threshold, add it to the list of candidates to
                # potentially add to the working set
                oli_interaction_relevance = self._relevance(active_set[item_id], isSearchingForDocs)
                if (oli_interaction_relevance > relevance_threshold):
                            oli_item_matches.append(item_id)

        # Now that we have changed the (e.g., attribute) weights based on the interaction, check 
        # each item (e.g., document) in the active set to see whether it is a candidate to 
        # be added to the working set
        if weights_delta == None or len(weights_delta) > 0:
            for item_id in active_set:
                # Ignore any documents already in the working set
                if item_id in working_set:    
                    continue
                
                interaction_relevance = 0
       
                # Calculate the relevance of the current item
                if weights_delta == None:
                    interaction_relevance = self._relevance(active_set[item_id], isSearchingForDocs)

                else:
                
                    # Iterate through each attribute in the document
                    iter_list = []
                    if isSearchingForDocs:
                        iter_list = active_set[item_id][DOC_ATTRIBUTES]
                    else:
                        iter_list = active_set[item_id][ATTRIBUTE_DOCS]
                    for item, value in iter_list.items():
                        if len(interaction_list) > 0:
                            if item in interaction_list:
                                interaction_relevance += interaction_list[item]*value
                        else:
                            interaction_relevance += interaction_list[item]*value  
                            
                # If this document has a positive interaction relevance, add
                # it to the list of candidates to be added to the working set
                if interaction_relevance > relevance_threshold:             
                    item_matches.append(item_id)


        """ This means that if I only find one item (e.g., document) in active set, 
        I will not pull any data from data controller  """
       
        if len(item_matches) > 0:
            # We have new candidates, so update the working set
            if not isTransitiveSearch and self._interaction != "oli":
                self._update_working_set(item_matches, view=isSearchingForDocs)
            else:
                self._update_working_set(item_matches, max_limit=self.transitive_new_limit, view=isSearchingForDocs)
                
        elif len(oli_item_matches) > 0:
            self._update_working_set(oli_item_matches, max_limit=self.transitive_new_limit, view=isSearchingForDocs)
        
        else:
            # We had no matches in the active set, so request more items
            # from upstream.
            # This is the mechanism by which a data controller or item store
            # model can add to items in the active set
            """ I have commented this code because in the current implementation 
            the active set is the same as the document set so we don't need to pull new documents
            it will be  a redundant process """
            """if len(attr_weights_delta) > 0 :
                # Let upstream models know about the updated weights
                data[ATTRIBUTE_RELEVANCE] = copy.copy(self._attr_weights)
                data[ATTRIBUTE_RELEVANCE_DELTA] = copy.copy(attr_weights_delta)
            """
            # Otherwise, either the search didn't match any items (e.g., attributes)
            # or we haven't loaded any items (e.g., attributes) from up stream, so pass
            # the search on, leaving the interaction in place

    # A helper function to update the working set of either documents or attributes
    def _update_working_set(self, candidates, max_limit=None, view=None):

        if view == None:
            print("Error: No view specified for _update_working_set")
            return
        
        if max_limit == None:
            max_limit = self.new_limit

        # Calculate the relevance for each candidate
        new_relevances = []
        
        for id in candidates:
            # For each document ID in candidates, calculate its relevance to
            # the active set. Keep relevances in a list.
            relevance = 0
            if(view):
                relevance = self._relevance(self._doc_active_set[id], view)
            else:
                relevance = self._relevance(self._attr_active_set[id], view)
            new_relevances.append((id, relevance))
       
        # Sort the newly calculated relevances in descending order to select
        # the most relevant documents to add to the working set
        new_relevances = sorted(new_relevances, key=lambda x: x[1], reverse=True)
        
        # Limit the number of new documents that will be added to the working
        # set to user defined limit
        limit = len(new_relevances)
        if max_limit < limit:
            limit = max_limit
                 
        # First remove documents if we will exceed the total working set limit
        removal = 0
        if view:
            removal = len(self._doc_working_set) + limit - self.working_limit
        else:
            removal = len(self._attr_working_set) + limit - self.working_limit

        if removal > 0:
            # Calculate the relevance of all documents in the working set
            current_relevances = []

            if(view):
                for doc_id in self._doc_working_set:
                    relevance = self._relevance(self._doc_working_set[doc_id], view)
                    current_relevances.append((doc_id, relevance))
            
            else:
                for attr_id in self._attr_working_set:
                    relevance = self._relevance(self._attr_working_set[attr_id], view)
                    current_relevances.append((attr_id, relevance))
                
            current_relevances = sorted(current_relevances, key=lambda x: x[1])
        
            # Remove the least relevant documents to make space for new documents
            for i in range(removal):
                id = current_relevances[i][0]

                if(view):
                    del self._doc_working_set[id]
                else:
                    del self._attr_working_set[id]
        
        # Now add the most relevant candidates to the working set and track them
        # Limit ourselves to a user defined number of new documents
        self._newly_added_docs = {}
        self._newly_added_attrs = {}
        for i in range(limit):
            id = new_relevances[i][0]

            if(view):
                self._doc_working_set[id] = self._doc_active_set[id]
                self._newly_added_docs[id] = self._doc_active_set[id]
            else:
                self._attr_working_set[id] = self._attr_active_set[id]
                self._newly_added_attrs[id] = self._attr_active_set[id]

    def reset(self):
        self._doc_working_set = {}
        self._attr_working_set = {}
        self._interaction = "none"
        self._docs_weights = {}
        self._weights = {}
        self._docs = set()
        self._attributes = set()
        #self._prototype = 0
