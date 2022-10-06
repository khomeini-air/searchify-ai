from tokenize import String
from py2neo import Graph
from fastapi import FastAPI
from pydantic import BaseModel,constr
import pandas as pd

app = FastAPI()

#use case 1
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

#use case 2
#make api to return all tags connected with required domain
class domain_obj(BaseModel):
    domain:str

@app.post('/tags')
async def tags(item:domain_obj):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    domain = item.domain

    #build quary body that return all tags acccording to specific domain
    tags_quary = '''
    MATCH (domain:Domain)<-[:IS_LINKED_WITH]->(tag:Tag)
    WHERE domain.name CONTAINS "''' +domain+ '''" 
    RETURN tag.name
    '''
    
    tags = graph.run(tags_quary)
    
    #converting the tabled result to dataframe to extract the tag names from it
    tags_pd = pd.DataFrame(tags.to_data_frame())
    
    #make condition in case there is no tag not send error but just send there is no tags available
    if tags_pd.empty:
        result_fi = {'tags':'No tags avaliable'}
    else:
        result_fi = {'tags':list(tags_pd['tag.name'])}
    return result_fi


class suggestions(BaseModel):
    domain:str
    tags: list[constr(max_length=255)]

#Build post function that will recive the data(domain,tags) and return the suggestions result
@app.post('/recommendations')
async def recommendatio(item:suggestions):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    #getting the domain and tags from item as it sent as json object
    domain = item.domain
    tags = item.tags

    #build quary body that contain the recommendation algorithm(content based recommendation algorithm) by adding domain and tags
    quary = '''
    MATCH (domain:Domain)<-[:IS_LINKED_WITH]->(tag:Tag)<-[:IS_LINKED_WITH]->(sug:Suggestion)
    WHERE domain.name CONTAINS "'''+domain+'''"
    WITH sug,COUNT(sug) AS suggestions
    ORDER BY suggestions DESC
    RETURN DISTINCT sug
    LIMIT 10
    '''
    #add first tag with AND
    tag = tags[0]
    tag_qu = ' AND tag.name CONTAINS "'+ tag +'"'
    substr = "WITH sug"
    idx = quary.index(substr)
    quary = quary[:idx] + tag_qu + quary[idx:]

    #adding other tags with OR 
    for tag in tags[1:]:
        tag_qu = ' OR tag.name CONTAINS "'+ tag+'"'
        substr = "WITH sug"
        idx = quary.index(substr)
        quary = quary[:idx] + tag_qu + quary[idx:]

    #run the quary and getiing the results
    result = graph.run(quary)
    
    #converting the tabled result to dataframe to extract the suggestions from it
    result_pd = pd.DataFrame(result.to_data_frame())
    
    #make condition in case there is no suggestions not send error but just send there is no suggestions
    if result_pd.empty:
        result_fi = {'suggestion':'No suggestions avaliable'}
    else:
        x=0
        result_fi = {}
        for sug in result_pd['sug']:
            result_fi['suggestion '+str(x)]=sug
            x+=1
    return result_fi