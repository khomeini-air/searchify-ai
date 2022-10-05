from py2neo import Graph
from fastapi import FastAPI
from pydantic import BaseModel,constr
import pandas as pd

app = FastAPI()


#Build get function that retarn all domains in database
@app.get('/domains')
async def domains():
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))


    #build quary body that return all domains
    quary = '''
    MATCH (n:Domain) RETURN n.name
    '''
    
    result = graph.run(quary)
    
    #converting the tabled result to dataframe to extract the domain names from it
    result_pd = pd.DataFrame(result.to_data_frame())
    
    #make condition in case there is no domain not send error but just send there is no domains available
    if result_pd.empty:
        result_fi = {'domains':'No domains avaliable'}
    else:
        result_fi = {'domains':list(result_pd['n.name'])}
    return result_fi