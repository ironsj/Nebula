"""This module contains the main logic for a pipeline, as well as parent
classes for any Data Controller, Model, or Connector that is created.
The Pipeline class represents an instance of a built pipeline. The
DataController, Model, and Connector classes contain instructions for 
developing new instances of each, and list out which functions can be
overridden to provide functionality."""

import argparse
import functools
import inspect
import queue
import sys
import threading
import time

import logging

sys.path.insert(0,"Nebula-Pipeline/nebula")

# Initialize the logging interface to log the timing info for each model function
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

fh = logging.FileHandler("pipeline.log")
fh.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh.setFormatter(formatter)
logger.addHandler(fh)

"""A dictionary data blob is passed between models in the pipeline to enable
communication between different pieces. These values represent keys into the 
dictionary passed around, or a key into a sublist or subdictionary. If two 
models use the same data key, they are expected to both understand that entry 
to mean the same thing. When developing new pipeline modules, new keys can be 
created to carry new types of data."""

# The list of documents passed through the forward pipeline
DOCUMENTS = "documents"
# The ID of each document within the document list
DOC_ID = "doc_id"
# The high dimensional position of each document within the document list
HIGHD_POSITION = "high_d"
# A map of attributes for each document within the document list, an 
# alternative way of storing high dimensional position 
DOC_ATTRIBUTES = "doc_attributes"
# The low dimensional projection of each document within the list
LOWD_POSITION = "low_d"
# The relevance of each document within the list
DOC_RELEVANCE = "doc_relevance"
# A dictionary of attribute names whose value is an index of the high dimensions
ATTRIBUTES = "attributes"
# A dictionary of attribute weights
ATTRIBUTE_RELEVANCE = "attr_relevance"
# A dictionary of attribute weight deltas from the most recent interaction
ATTRIBUTE_RELEVANCE_DELTA = "attr_relevance_delta"
# A list of weights for the similarity of attributes
SIMILARITY_WEIGHTS = "similarity_weights"
# An interaction, whose value is a string specifying the type of interaction
INTERACTION = "interaction"
# Raw text for testing
RAW_TEXT = "raw_text"
# Weights from iMDS
TOPIC_WEIGHTS = "topic_weights"
# Induced word weights
WORD_WEIGHTS = "word_weights"
# Document topic distribution
DOC_TOPICS = "doc_topics"

# The list of attributes passed through the forward pipeline
ATTRIBUTE_LIST  = "attr_list"
ATTRIBUTE_ID="attr_id"
#A map of documents  for each attribute (List of docuements that contain this attribute)
ATTRIBUTE_DOCS = "attribute_docs"
# A dictionary of document names whose value is an index of the high dimensions
DOCUMENTS_LIST  = "documents_list"
# A key in the data blob dictionary to get the view (observation = True, or
# attribute = False) to determine which panel in TwoView is being interacted with
VIEW = "view"
# A dictionary of additional interaction parameters
# INTERACTION_PARAMS = "interaction_params"


class Pipeline:
    """This class represents the entire pipeline structure for data and interaction
    processing. A pipeline consists of a Data Controller, series of Models, and
    a Connector. Each of these pieces has a base class defined within this module.
    """
    
    def __init__(self):
        """Initiate a pipeline object. Endow it with a null or empty: models,
        data controller, connector, background thread queue, threading lock.
        """

        # Note: Order of models is important, because order of operation on models
        # matters.
        self._models = []
        self._data_controller = None
        self._connector = None
   
        # Create an asynchronous queue for holding data blobs waiting to be
        # fetched by the asynchronous models.
        self._async_queue = queue.Queue()
        
        # Creates a lock for the synchronous portion of the pipeline.
        self._lock = threading.Lock()
        
        # Initialize a timing info dictionary that will contain information
        # about the running times for the models. Useful for debugging.
        self._timing_info = {}
        
    def insert_model(self, index, m):
        """Inserts a model into the pipeline at a specific index."""
        
        # All inserted models must extend the base Model class defined below
        if not isinstance(m, Model):
            raise TypeError("Only Model objects can be inserted into the main models")
        
        # If the model is an asynchronous model, setup the callbacks to make
        # the push behavior possible.
        if isinstance(m, AsyncModel):
            m._push_callback = functools.partial(self.push, model=m)
        
        self._models.insert(index, m)
        
    def append_model(self, m):
        """Appends a model to the end of the pipeline."""
        
        # All inserted models must extend the base Model class defined below
        if not isinstance(m, Model):
            raise TypeError("Only Model objects can be inserted into the main models")

        # If the model is an asynchronous model, setup the callbacks to make
        # the push behavior possible.       
        if isinstance(m, AsyncModel):
            m._push_callback = functools.partial(self.push, model=m)
        
        self._models.append(m)
        
    def delete_model(self, index):
        """Removes a model from the pipeline at the specified index."""
        
        if index not in list(range(len(self._models))):
            raise IndexError("Invalid index to delete model")
        
        self._models.pop(index)
        
    def get_model(self, index):
        """Returns the model in the pipeline at the specified index."""
        
        if index not in list(range(len(self._models))):
            raise IndexError("Invalid index to delete model")
        
        return self._models[index]
    
    def set_data_controller(self, dc):
        """Sets the data controller to use for the pipeline."""
        
        self._data_controller = dc  
       
        # Set the callback in the connector for the Data Controller's
        # get method
        if self._connector:  
           self._connector.set_callbacks(get=dc.get)
           
        """  functools.partial:Return a new partial object which when called will behave like func called with the positional arguments args and keyword arguments keywords. If more arguments are supplied to the call, they are appended to args. If additional keyword arguments are supplied, they extend and override keywords   """
        
        # by doing this we have a new object with a simplified signature
        dc._push_callback = functools.partial(self.push, dc=dc)
        
    def set_connector(self, connector):
        """Sets the connector (nebula defined connector) to use for the 
        pipeline, and sets the callback methods for the connector."""
        
        self._connector = connector
        self._connector.set_callbacks(update=self.run, reset=self.reset)
        if self._data_controller:
           self._connector.set_callbacks(get=self._data_controller.get)
        
    def validate(self):
        """Validate the pipeline, checking input and output requirements of 
        each model in the pipeline, as well as correct async setup and
        parameter names."""
 
        # First check input/output requirements
        # If the order of models added to the _models list is out of the necessary
        # order, throw an error
        forward = set(self._data_controller.output())
        for m in self._models:
            if not set(m.forward_input_reqs()) <= forward:
                raise TypeError("Model %s did not have forward reqs met" % m)
               
            forward |= set(m.forward_output())
              
        inverse = set([INTERACTION])
             
        for m in reversed(self._models):
            if not set(m.inverse_input_reqs()) <= inverse:
                raise TypeError("Model %s did not have inverse reqs met: %s" % (m, set(m.inverse_input_reqs()) - inverse))
            
            inverse |= set(m.inverse_output())
            
        if not set(self._data_controller.input_reqs()) <= inverse:
            raise TypeError("Data controller did not have inverse reqs met")
        
        # Now check to make sure there are no non-async models closer to the
        # data controller than the async models
        non_async_found = False
        for m in self._models:
            if not isinstance(m, AsyncModel):
                non_async_found = True
            elif non_async_found:
                raise TypeError("Async model %s did located after non-async model", m)
            
        # Finally, check the parameters to make sure each has a unique name
        params = set()
        for m in self._models:
            for param in m.get_params():
                if param["name"] in params:
                    raise TypeError("Duplicate parameter name found: %s", param["name"])
       
                params.add(param["name"])
               
    def start(self, argv=None):
        """Starts the pipeline. Creates a mapping of all potential parameters
        in the pipeline. If argv is provided, these arguments are used to
        set parameters within the pipeline. The pipeline is able to call _setup_ 
        functions from any and all objects of the Model class in the pipeline.
        For example, it will call _setup_ for the Data Controller, followed
        by _setup_ for each Model. Here, a single data blob object is
        passed using each _setup_ function. The data blob is passed in the same
        manner in each iteration of the pipeline. If any asynchronous
        Models exist in the pipeline, the background thread is started. Finally,
        the Connector is started to listen for connections."""
       
        self.validate()

        # Get all the parameters available in the models
        # Command line arguments are defined by each Model subclass
        self._params = {}
        self._param_mapping = {}
        # Check all Models to see what parameters they accept
        for m in self._models:
            for param in m.get_params():
                self._param_mapping[param["name"]] = m
                self._params[param["name"]] = param 
                
        if argv:
            parser = argparse.ArgumentParser()
            for param in self._params:
                parser.add_argument("--" + self._params[param]["name"], action="store",
                                    default=argparse.SUPPRESS)
            args = vars(parser.parse_args(argv))
            for arg in args:
                model = self._param_mapping[arg]
                current_type = type(model.get(arg))
                new_value = current_type(args[arg])
                model.set(arg, new_value)

        # Initial data blob (setup_data) for the pipeline. If the data controller chooses to 
        # start with some initial data set, pass this data to the models
        # (e.g. ActiveSetModel or SimilarityModel)
        setup_data = {}
        self._data_controller.setup(setup_data)
        if ATTRIBUTES in setup_data:
            Model.global_weight_vector = {attr: 1.0/len(setup_data[ATTRIBUTES])  for attr in list(setup_data[ATTRIBUTES].keys())}
            # for SIRIUS
            Model.global_attribute_weight_vector = {attr: 1.0/len(setup_data[ATTRIBUTES]) for attr in list(setup_data[ATTRIBUTES].keys())}
        
        if   DOCUMENTS_LIST  in setup_data:
             Model.global_document_weight_vector ={doc: 1.0/len(setup_data[DOCUMENTS_LIST]) for doc in list(setup_data[DOCUMENTS_LIST].keys())}
         
        for model in self._models:
            # Each call of model.setup changes setup_data at this scope.
            # i.e. if the first call of model.setup deletes fields within
            # setup_data, those fields will not be present during the second
            # call of model.setup => Call by reference 
            model.setup(setup_data)
          
        # Find the last model that is asynchronous
        self._async_index = -1
         
        # Model list should be ordered [async_model, ...,async_model, reg_model,...,reg_model]    
        # Check if we have any asynchronous Models. Get index of last async_model.            
        for i in range(len(self._models)):
            if not isinstance(self._models[i], AsyncModel):
                self._async_index = i - 1
                break
        
        if self._async_index >= 0:
            # Start the asynchronous thread if an asynchronous model exists
            self._async_thread = threading.Thread(target=self._async)
            self._async_thread.daemon = True
            self._async_thread.start()
  
    def run(self, data):
        """Executes an iteration of the pipeline, starting with the inverse
        algorithms. The inverse algorithms are executed in the reverse order
        that they were added to the pipeline. When all inverse algorithms have
        been executed, the Data Controller's run function is executed with the
        cumulative data from the inverse functions. Then the forward functions
        for each Model are executed in the order they were added to the pipeline,
        with the data returned from the Data Controller.
        
        Models' inverse algorithms may also short circuit, which causes the same 
        Model's forward algorithm to be executed with the short circuit data, 
        and the pipeline continuing from that point."""
        
        logger.info("Executing pipeline\nData: %s", data)
        
        # Acquires the thread lock for the synchronous portion of the pipeline
        with self._lock:
            forward_data = {}
            
            i = len(self._models) - 1
            short_circuit_data = None
            
            # Run each inverse model until we short circuit or run every model
            # I have commented the short_circuit_data condition because we need to go through the whole pipeline
            while i >= 0: # and short_circuit_data is None:
                # If we have reached an async model, push the data on the async
                # queue to be processed in a separate thread
                if isinstance(self._models[i], AsyncModel):
                    self._async_queue.put(data)
                    break
                
                # inverse functions can return a new data blob if there is a need
                # to short circuit which is stored in short_circuit_data.
                # SEE ADAM'S THESIS FOR MORE ON SHORT CIRCUITING 
                # _time_func tracks the running time of the function but returns
                # the return value of the inverse function call
                short_circuit_data = self._time_func(self._models[i].inverse, data)    

                i -= 1
                
            # If we've short circuited, set that data as the forward data blob
            if short_circuit_data is not None:
                forward_data = short_circuit_data
            elif i < 0:
                # If we haven't short circuited and haven't hit an AsyncModel,
                # run the data controller
                # Set the forward_data blob to the return value of the data
                # controller
                forward_data = self._time_func(self._data_controller.run, data)  
            
            # Run all forward models, either from the beginning or from where
            # we short circuited
            i += 1
            while i < len(self._models):
                self._time_func(self._models[i].forward, forward_data)
                i += 1
    
            # Log this iteration of timing information for each function
            self._record_timing()
    
            # Return the processed data from all forward functions to the
            # connector (usually for the visualization)
            return forward_data
        
    def _time_func(self, func, *args, **kwargs):
        """Times a function and stores min, max, and average running time
        for a specific instance method of a class type."""
      
        if not inspect.ismethod(func):
            raise TypeError("Timed function must be instance method")
        
        # Record the start time for the function
        start_time = time.time()
        
        # Execute the function
        ret_val = func(*args, **kwargs)
        
        # Get the execution time
        exec_time = time.time() - start_time
        
        # Get the timing info for the class
        cls = func.__self__.__class__.__name__
        if cls not in self._timing_info:
            self._timing_info[cls] = {}
            
        cls_dict = self._timing_info[cls]
        
        # Get the specific timing info for this method
        func_name = func.__name__
        if func_name not in cls_dict:
            cls_dict[func_name] = TimingInfo()
            
        # update that timing info
        cls_dict[func_name].update(exec_time)

        return ret_val
    
    def _record_timing(self):
        """Records the timing info for all methods currently held in the
        timing info object."""
        
        log_entry = "Timing info\n"
        
        for m in self._timing_info:
            for func in self._timing_info[m]:
                info = self._timing_info[m][func]
                
                log_entry += "%s.%s average time: %f seconds\n" % (m, func, info.average)
                log_entry += "%s.%s max time: %f seconds\n" % (m, func, info.max)
                
        logger.info(log_entry)
    
    def push(self, data, model=None, dc=None):
        """Relevant for asynchronous models and data controllers. Receives 
        data from an async model or data controller and pushes it down the 
        pipeline, sending the results to the client."""
        
        # Define the behavior as its own function so we can run it on a new
        # thread
        def func():
            # If the push is from the data controller, start with the first model
            i = 0
            if model:
                # Otherwise start with the model after where the push originated
                i = self._models.index(model) + 1
            
            while i <= self._async_index:
                self._time_func(self._models[i].forward, data)
                i += 1
                
            # Only execute the synchronous portion of the pipeline while
            # holding the pipeline lock
            with self._lock:
                while i < len(self._models):
                    self._time_func(self._models[i].forward, data)
                    i += 1
                
                self._record_timing()
                
            self._connector.push_update(data)
            
        # Start a new thread to execute the push
        threading.Thread(target=func).start()

    def _async(self):
        """The background thread that processes the asynchronous model
        functions. The behavior is very similar to the run method."""
     
        while True:
            # Retrieve the next piece of data off the queue
            data = self._async_queue.get(True)
            
            # End this thread if we get a None object
            if data is None:
                self._async_queue.task_done()
                break
            
            i = self._async_index
            short_circuit_data = None
            forward = {}
            
            # Run all AsyncModels, or until we short circuit
            while i >= 0 and not short_circuit_data:
                short_circuit_data = self._models[i].inverse(data)
                i -= 1
                
            # Set the forward data to the short circuited data
            if short_circuit_data:
                forward = short_circuit_data
            elif i < 0:    
                # If we haven't short circuited, run the inverse model
                forward = self._data_controller.run(data)
                
            # Run all forward AsyncModels
            i += 1
            while i <= self._async_index:
                self._models[i].forward(forward)
                i += 1
    
            # Run the first non-AsyncModel, using the pipeline lock to insure
            # no threading issues
            with self._lock:
                self._models[i].forward(forward)
                
            self._async_queue.task_done()

    def reset(self):
   
        """Resets the pipeline, resetting all models and the data controller.
        The setup for each is then run just as in the start function."""
        
        # Make sure all tasks in the queue are complete so we don't have any
        # threading issues.
        self._async_queue.join()
        
        for model in self._models:
            model.reset()
            
        self._data_controller.reset() # why he called this make no sense
        
        # Now rerun the setup
        setup_data = {}
        self._data_controller.setup(setup_data)

        """ I need to redefine the the model.global vector here """
        if ATTRIBUTES in setup_data:
            Model.global_weight_vector = { attr: 1.0/len(setup_data[ATTRIBUTES]) for attr in list(setup_data[ATTRIBUTES].keys()) }
            # for SIRIUS
            Model.global_attribute_weight_vector = {attr: 1.0/len(setup_data[ATTRIBUTES]) for attr in list(setup_data[ATTRIBUTES].keys())}
          
        if   DOCUMENTS_LIST  in setup_data:
             Model.global_document_weight_vector ={doc: 1.0/len(setup_data[DOCUMENTS_LIST]) for doc in list(setup_data[DOCUMENTS_LIST].keys())}
       
        for model in self._models:
            model.setup(setup_data)
     
       
         
class Model(object):
    """A model represents one logical piece of the data processing. 
    Each model is made up of two core pieces, a forward algorithm for converting
    a list of documents to a visualization, and an inverse algorithm for
    converting an interaction into changes in the model.
    
    Additionally, to help ensure a main is valid, each model must specify
    what inputs are required for the forward and inverse algorithms, currently
    in the form of a string name of a certain variable. If the output of one
    model uses the same name as the input to the next model, it is assumed that
    these models are valid together and understand what that variable
    represents. Later this may be changed to be more robust.
    """
    
    # A list of all parameters that can be modified at run time. This object
    # should be a dictionary that maps variable names to descriptors. i.e.
    # params = {"max_count": "Max documents"}
    params = {}
    
    #Global weight vector shared between relevance and similarity models 
    #This is better than having a global vairable. Both subclasses can easily access
    #this class variable
    global_weight_vector = {}
    global_attribute_weight_vector = {}
    global_document_weight_vector = {}
    
    # These functions should not be overridden
    def get_params(self):     
        return [{"name": k, "description": self.params[k], "value": getattr(self, k)} for k in self.params]
    
    def get(self, attr):
        return getattr(self, attr)
    
    def set(self, attr, value):
        setattr(self, attr, value)

    # Overwrite the following methods to create a new model
    def setup(self, data):
        """Perform any setup tasks with data from upstream models and the
        data controller."""
        pass
    
    def forward(self, data):
        """The forward algorithm to run with data from upstream models and
        the data controller.
        """
        pass
    
    def inverse(self, data):
        """The inverse algorithm to run. This will contain the interaction data
        as well as any additional data from models closer to the connector.
        """
        pass
    
    def forward_input_reqs(self):
        """The requirements this model has for the forward algorithm."""
        return []
    
    def forward_output(self):
        """The output the forward algorithm has for this model."""
        return []
    
    def inverse_input_reqs(self):
        """The requirements this model has for the inverse algorithm."""
        return []
    
    def inverse_output(self):
        """The output the inverse algorithm has for this model."""
        return []
    
    def reset(self):
        """Reset this model to it's initial state."""
        pass
    
    
    
class AsyncModel(Model):
    """An asynchronous model can run background threads and generate
    updates that will propagate down the pipeline until a non asynchronous
    model is encountered."""
    
    """A callback set by the pipeline to accept pushes from async models down
    the pipeline."""
    
    _push_callback = None
    
    def push(self, data):
        """Subclasses can call this function to push an async update down the
        pipeline."""
        
        if self._push_callback is not None:
            self._push_callback(data)
        else:
            raise Exception("No push callback was set")
       
        

class DataController(object):
    """A data controller exists at the end of the pipeline opposite the
    visualization. After an interaction and all inverse models have been run,
    the data controller receives data from the models and interaction. It has only one main
    algorithm, which has the same type of input requirements as the models.
    The output is typically a list of documents, with certain info about each
    document.
    """
    
    def input_reqs(self):
        """What the data controller expects as input to its execution."""
        return []
    
    def output(self):
        """What the data controller outputs after its execution."""
        return []
    
    def get(self, args):
        """Retrieves a piece of data directly from the data controller without
        going through the pipeline. Typically arguments may be:
        
        args["id"]: the ID of the document to retrieve a piece of data from
        args["type"]: the type of data to retrieve, such as "raw"
        """
        pass
    
    def setup(self, data):
        """Performs any initial setup before accepting input."""
        pass
    
    def run(self, data):
        """Executes an iteration of the data controller's algorithm. The value
        returned from this function is the value used for the `data` argument
        for subsequent forward function calls in the pipeline's models."""
        pass
    
    def push(self, data):
        """Subclasses can call this function to push an async update down the
        pipeline."""
        if self._push_callback is not None:
            self._push_callback(data)
        else:
            raise Exception("Push callback not set")
    
    def reset(self):
        """Resets the data controller to its initial state."""
        pass
    
class Connector(object):
    """A connector connects the pipeline to a visualization or visualization
    controller. It typically implements some sort of socket, and connects out
    to or receives connections from an external source.
    """
    
    def set_callbacks(self, update=None, get=None, set=None, reset=None):
        pass
    
    def start(self):
        pass
    
    def push_update(self, data):
        pass
        
class TimingInfo:
    """Stores timing info for a single method. This timing info includes the
    minimum, maximum and average running times."""
    
    def __init__(self):
        self.average = 0.0
        self.min = -1
        self.max = 0
        self._count = 0
        
    def update(self, execution_time):
        """Updates this timing object with a new execution time."""
        if execution_time > self.max:
            self.max = execution_time
            
        if execution_time < self.min or self.min == -1:
            self.min = execution_time
            
        self.average *= float(self._count) / (self._count + 1)
        self._count += 1
        self.average += float(execution_time) / self._count
