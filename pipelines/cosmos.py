import os
import sys
import asyncio

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

from nebula.connector import SocketIOConnector
from nebula.data_controller.CSVDataController import CSVDataController
from nebula.model.ActiveSetModel import ActiveSetModel
from nebula.model.SimilarityModel import SimilarityModel
from nebula.pipeline import Pipeline

# import zerorpc

async def main():
    if len(sys.argv) < 4:
        print("Usage: python main.py <port> <csv file path> <raw data folder path> <pipeline arguments>")
    
 
    csvfile = sys.argv[2]
    raw_folder = sys.argv[3]
    
    # Initiate a pipeline instance
    pipeline = Pipeline()
    
    # Create an ActiveSetModel object from the nebula.model module, starts out empty
    relevance_model = ActiveSetModel()
    
    ### Continue from here
    
    # Create a SimilarityModel object from the nebula.model module, which does 
    # forward and inverse MDS
    # projections and stores the current set of similarity weights
    similarity_model = SimilarityModel()
    
    # Create a CSVDataController object from the nebula.data module, providing
    # a CSV file to load data from and the path to a folder containing the raw
    # text for each document. 
    # IMPORTANT: The CSV file should not be changed hereafter
    data_controller = CSVDataController(csvfile, raw_folder)
    
    # Next we add the models to the pipeline. New models would be added here.
    # The order that the models are
    # added is the order in which they are executed in the forward pipeline.
    # IMPORTANT: They are executed in reverse order in the inverse pipeline
    pipeline.append_model(relevance_model)
    pipeline.append_model(similarity_model)
    
    # Note: a pipeline contains exactly one data controller
    pipeline.set_data_controller(data_controller)

    connector = SocketIOConnector(port=int(sys.argv[1]))
    
    # Note: a pipeline contains exactly one connector
    pipeline.set_connector(connector)

    await connector.makeConnection(port=int(sys.argv[1]))
    
    pipeline.start(sys.argv[4:])
    
if __name__ == "__main__":
    asyncio.run(main())