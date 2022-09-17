from py2neo import Graph
from fastapi import FastAPI
from pydantic import BaseModel,constr
import pandas as pd

app = FastAPI()

class suggestions(BaseModel):
    domain:str
    tags: list[constr(max_length=255)]


@app.post('/')
async def recommendatio(item:suggestions):
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))
    # item_dict = json.load(item)
    domain = item.domain
    tags = item.tags

    quary = '''
    MATCH (domain:Domain)<-[:IS_LINKED_WITH]->(tag:Tag)<-[:IS_LINKED_WITH]->(sug:Suggestion)
    WHERE domain.name CONTAINS "'''+domain+'''"
    WITH sug,COUNT(sug) AS suggestions
    ORDER BY suggestions DESC
    RETURN DISTINCT sug.name
    LIMIT 10
    '''
    tag = tags[0]
    tag_qu = ' AND tag.name CONTAINS "'+ tag +'"'
    substr = "WITH sug"
    idx = quary.index(substr)
    quary = quary[:idx] + tag_qu + quary[idx:]
    for tag in tags[1:]:
        tag_qu = ' OR tag.name CONTAINS "'+ tag+'"'
        substr = "WITH sug"
        idx = quary.index(substr)
        quary = quary[:idx] + tag_qu + quary[idx:]

    result = graph.run(quary)
    
    result_pd = pd.DataFrame(result.to_data_frame())
    # print('this is the empty dataframe',result_pd)
    if result_pd.empty:
        result_fi = {'suggestion':'No suggestions avaliable'}
    else:
        result_fi = {'suggestion':list(result_pd['sug.name'])}
    return result_fi