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
from nebula.data_controller.TwitterDataController import TwitterDataController
from nebula.model.ActiveSetModel import ActiveSetModel
from nebula.model.SimilarityModel import SimilarityModel
import asyncio

async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <port> <pipeline arguments>")
    
    access_token = "22705576-1RXheyykqon2L6DgUIBtLcqrqeyb5PzIAiTpkN2Eh"
    access_token_secret = "lBX6JsFWkB1vYM0V3RHQjuWz9gclBc4ZvWACerDTB8O8h"
    consumer_key = "eNHZNhaOd0QFkCwKqb2si9Of5"
    consumer_secret = "Ltj6z3BkDanYnjqZwXCcNKiBSu7MoxUrJrHZgPUsnmBSBVoUNu"
    
    pipeline = Pipeline()
   
    relevance = ActiveSetModel()
    similarity = SimilarityModel()
    data_controller = TwitterDataController(access_token=access_token,
                                                        access_token_secret=access_token_secret,
                                                        consumer_key=consumer_key,
                                                        consumer_secret=consumer_secret)
   
    pipeline.append_model(relevance)
    pipeline.append_model(similarity)
    pipeline.set_data_controller(data_controller)
    
    connector = SocketIOConnector(port=int(sys.argv[1]))
    pipeline.set_connector(connector)
    
    await connector.makeConnection(port=int(sys.argv[1]))
    
    pipeline.start(sys.argv[2:])
    
if __name__ == "__main__":
    asyncio.run(main())