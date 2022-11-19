import os
import sys

# Most recent version of Python3 needs some help to find reletive paths to modules.
# The follwoing three lines will ensure that Python3 will be able to find the modules
# that are needed in this file.
script_dir = os.path.dirname( __file__ )
nebula_pipeline_dir = os.path.join( script_dir, '..', 'Nebula-Pipeline')
sys.path.append(nebula_pipeline_dir)
data_controller_dir = os.path.join( script_dir, '..', 'Nebula-Pipeline', 'data_controller')
sys.path.append(data_controller_dir)
model_dir = os.path.join( script_dir, '..', 'Nebula-Pipeline', 'model')
sys.path.append(model_dir)

from nebula.pipeline import Pipeline
from nebula.connector import SocketIOConnector
from nebula.data_controller.TwoView_CSVDataController import TwoView_CSVDataController
from nebula.model.ImportanceModel import ImportanceModel
from nebula.model.TwoView_SimilarityModel import TwoView_SimilarityModel
import asyncio

async def main():
    if len(sys.argv) < 4:
        print("Usage: python main.py <port> <csv file path> <raw data folder path> <pipeline arguments>")
    
    csvfile = sys.argv[2]
    raw_folder = sys.argv[3]
    
    pipeline = Pipeline()
    
    #Create an ImportanceModel object from the nebula.model module, starts out empty
    relevance_model = ImportanceModel(should_query=True)
   
    # Create a SimilarityModel object from the nebula.model module, which does 
    # forward and inverse MDS
    # projections and stores the current set of similarity weights
    similarity_model = TwoView_SimilarityModel(dist_func="euclidean")
    
    
    data_controller = TwoView_CSVDataController(csvfile, raw_folder)
    
    pipeline.append_model(relevance_model)
    pipeline.append_model(similarity_model)
    
    # Note: a pipeline contains exactly one data controller
    pipeline.set_data_controller(data_controller)
    
    connector = SocketIOConnector(port=int(sys.argv[1]))
    
    # Note: a pipeline contains exactly one connector
    pipeline.set_connector(connector)
    
    # Following line creates a connection between the Python3 code and JS code
    await connector.makeConnection(port=int(sys.argv[1]))
    
    # Starts the pipeline, running the setup for the data controller and each
    # model, and then tells the connector to start listening for connections.
    # The pipeline can take command line arguments to set user defined model
    # parameters.
    pipeline.start(sys.argv[4:])
    
if __name__ == "__main__":
    asyncio.run(main())