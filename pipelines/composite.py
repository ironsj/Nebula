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
from nebula.data_controller.CSVDataController import CSVDataController
from nebula.model.ActiveSetModel import ActiveSetModel
from nebula.model.CompositeModel import CompositeModel
import asyncio

async def main():
    if len(sys.argv) < 4:
        print("Usage: python main.py <port> <csv file path> <raw data folder path> <pipeline arguments>")
    
    csvfile = sys.argv[2]
    print(csvfile)
    raw_folder = sys.argv[3]
    
    pipeline = Pipeline()
   
    relevance = ActiveSetModel()
    composite = CompositeModel()
    data_controller = CSVDataController(csvfile, raw_folder)
   
    pipeline.append_model(relevance)
    pipeline.append_model(composite)
    pipeline.set_data_controller(data_controller)
    
    connector = SocketIOConnector(port=int(sys.argv[1]))
    pipeline.set_connector(connector)
    
    await connector.makeConnection(port=int(sys.argv[1]))
    
    pipeline.start(sys.argv[4:])
    
if __name__ == "__main__":
    asyncio.run(main())