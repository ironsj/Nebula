import sys
import zerorpc
import os

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
    if len(sys.argv) < 2:
        print("Usage: python main.py <port> <csv file path> <raw data folder path> <pipeline arguments>")
   
    
    pipeline = Pipeline()
   
    relevance = ActiveSetModel()
    similarity = TopicSimilarityModel()
    topic_model = TopicModel()
    data_controller = ESController()
    tfModel = TFModel()


    pipeline.append_model(tfModel)
    pipeline.append_model(relevance)
    pipeline.append_model(topic_model)
    pipeline.append_model(similarity)
    pipeline.set_data_controller(data_controller)
    
    connector = SocketIOConnector(port=int(sys.argv[1]))

    pipeline.set_connector(connector)

    await connector.makeConnection(port=int(sys.argv[1]))
    
    pipeline.start(sys.argv[2:])
    
if __name__ == "__main__":
    asyncio.run(main())
