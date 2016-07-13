import nebula.connector
import nebula.data
import nebula.model
import nebula.pipeline

import sys
import zerorpc

def main():
    if len(sys.argv) < 2:
        print "Usage: python main.py <port> <pipeline arguments>"
    
    pipeline = nebula.pipeline.Pipeline()
   
    relevance = nebula.model.DynamicActiveSetModel()
    similarity = nebula.model.DynamicSimilarityModel()
    data_controller = nebula.data.TwitterDataController()
   
    corpus = nebula.model.CorpusSetModel()
    #pipeline.append_model(corpus)
   
    pipeline.append_model(relevance)
    pipeline.append_model(similarity)
    #pipeline.append_model(composite)
    pipeline.set_data_controller(data_controller)
    
    connector = nebula.connector.ZeroMQConnector(port=int(sys.argv[1]))
    pipeline.set_connector(connector)
    
    pipeline.start(sys.argv[2:])
    
if __name__ == "__main__":
    main()