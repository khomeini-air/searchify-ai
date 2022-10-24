from re import L
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
async def recommendations(item:suggestions):
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


############################## ADMIN APIS #####################################

#use case 1
######################### CRUD for domain #########################
#api for create new domain
class new_domain(BaseModel):
    domain:str
    visability:bool

@app.post('/admin_create_domain')
async def create_domain(item:new_domain):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    domain_name = item.domain
    domain_visability = item.visability
    #build quary body that return all domains
    quary = '''MERGE (n:Domain {name: "'''+domain_name+'''",visibility:"'''+str(domain_visability)+'''"}) RETURN n.name'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the domain names from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case domain not added sucessfuly return the crate domain process failed
    if result_pd.empty:
        result_fi = {'domains':'create domain process failed'}
    else:
        result_fi = {'domains':list(result_pd['n.name'])[0]+' domain added sucessfully'}

    return result_fi


#api for read required domain
class read_domain(BaseModel):
    domain:str
    

@app.post('/admin_read_domain')
async def read_domain_fun(item:read_domain):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    domain_name = item.domain
   
    #build quary body that read the required domain
    quary = '''MATCH (n:Domain {name: "'''+domain_name+'''"}) RETURN n'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the domain data from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case domain not read sucessfuly return the read domain process failed
    if result_pd.empty:
        result_fi = {'domain':'read domain process failed'}
    else:
        result_fi = {'domain':result_pd['n']}

    return result_fi

#api for udate required domain
class update_domain(BaseModel):
    domain_old_name:str
    domain_new_name:str
    domain_visability:bool

@app.post('/admin_update_domain')
async def update_domain_fun(item:update_domain):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    domain_name = item.domain_old_name
    domain_new_name = item.domain_new_name
    domain_visability = item.domain_visability
   

    #build quary body that update the domain properties
    quary = '''MATCH (n:Domain {name: "'''+domain_name+'''"}) SET n.name = "'''+domain_new_name+'''" , n.visability ='''+str(domain_visability)+''' RETURN n.name'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the domain names from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case domain not added sucessfuly return the crate domain process failed
    if result_pd.empty:
        result_fi = {'domain':'update domain process failed'}
    else:
        result_fi = {list(result_pd['n.name'])[0]+' domain updated sucessfully'}

    return result_fi

#api for delete required domain
class delete_domain(BaseModel):
    domain:str

@app.post('/admin_delete_domain')
async def delete_domain_fun(item:delete_domain):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    domain_name = item.domain

    #build quary body that return all domains
    quary = '''MATCH (n:Domain {name: "'''+domain_name+'''"}) DETACH DELETE n'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the domain names from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case domain not added sucessfuly return the crate domain process failed
    if result_pd.empty:
        result_fi = {'domains':'Required domain deleted sucessfully'}
    else:
        result_fi = {'domains':'delete domain process failed'}

    return result_fi


######################### CRUD for Tags #########################
#api for create new tag
class new_tag(BaseModel):
    tag:str
    domain:str


@app.post('/admin_create_tag')
async def create_tag_fun(item:new_tag):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    tag_name = item.tag
    domain_name = item.domain
    #build quary body that return required tag
    tag_merging_quary = '''MERGE (tag:Tag {name: "'''+tag_name+'''"})'''
    relation_wdomain_quary = '''MATCH (t:Tag {name: "'''+tag_name+'''"}) MATCH (d:Domain {name: "'''+domain_name+'''"}) MERGE (t)- [:IS_LINKED_WITH] ->(d) RETURN t.name,d.name'''
    graph.run(tag_merging_quary)
    relation_result = graph.run(relation_wdomain_quary)

    #converting the tabled result to dataframe to extract the tag name from it
    result_pd = pd.DataFrame(relation_result.to_data_frame())

    #make condition in case tag not added sucessfuly return the create tag process failed
    if result_pd.empty:
        result_fi = {'tag':'create tag process failed'}
    else:
        result_fi = {'tags':list(result_pd['t.name'])[0]+' tag added sucessfully and attach to '+list(result_pd['d.name'])[0]+' domain sucessfully'}

    return result_fi


#api for read required tag
class read_tag(BaseModel):
    tag:str
    

@app.post('/admin_read_tag')
async def read_tag_fun(item:read_tag):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    tag_name = item.tag
   
    #build quary body that read the required tag
    quary = '''MATCH (t:Tag {name: "'''+tag_name+'''"}) <-[:IS_LINKED_WITH]-> (d:Domain) RETURN t,d'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the tag data from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case tag not read sucessfuly return the read tag process failed
    if result_pd.empty:
        result_fi = {'tag':'read tag process failed'}
    else:
        result_fi = {'tag':result_pd['t'],'domain':result_pd['d']}

    return result_fi

#api for udate required tag
class update_tag(BaseModel):
    tag_old_name:str
    tag_new_name:str
    old_related_domain:str
    new_related_domain:str

@app.post('/admin_update_tag')
async def update_tag_fun(item:update_tag):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    tag_old_name = item.tag_old_name
    tag_new_name = item.tag_new_name
    old_related_domain = item.old_related_domain
    new_related_domain = item.new_related_domain
   
    #build quary body that update the tag properties and it's relation
    quary = '''MATCH (n:Tag {name: "'''+tag_old_name+'''"}) SET n.name = "'''+tag_new_name+'''" '''
    erase_old_relation_quary = '''MATCH (t:Tag {name: "'''+tag_new_name+'''"}) - [r:IS_LINKED_WITH] -> (d:Domain {name: "'''+old_related_domain+'''"}) DELETE r'''
    relation_wdomain_quary = '''MATCH (t:Tag {name: "'''+tag_new_name+'''"}) MATCH (d:Domain {name: "'''+new_related_domain+'''"}) MERGE (t)- [:IS_LINKED_WITH] ->(d) RETURN t.name,d.name'''
    
    graph.run(quary)
    graph.run(erase_old_relation_quary)
    result = graph.run(relation_wdomain_quary)

    #converting the tabled result to dataframe to extract the tag name from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case tag not updated sucessfuly return the update tag process failed
    if result_pd.empty:
        result_fi = {'tag':'update tag process failed'}
    else:
        result_fi = {'tags':list(result_pd['t.name'])[0]+' tag updated sucessfully and attach to '+list(result_pd['d.name'])[0]+' domain sucessfully'}

    return result_fi

#api for delete required domain
class delete_tag(BaseModel):
    tag:str

@app.post('/admin_delete_tag')
async def delete_tag_fun(item:delete_tag):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    tag_name = item.tag

    #build quary body detach and delete the required tag
    quary = '''MATCH (n:Tag {name: "'''+tag_name+'''"}) DETACH DELETE n'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the tag name from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case tag not deleted sucessfuly return the delete tag process failed (result must be empty)
    if result_pd.empty:
        result_fi = {'tags':'Required tag deleted sucessfully'}
    else:
        result_fi = {'tags':'delete tag process failed'}

    return result_fi


######################### CRUD for Recommendations #########################
#api for create new suggestion
class new_rec(BaseModel):
    rec:str
    rec_dis:str
    rec_key:str
    rec_sh_count:str
    rec_title:str
    domain:str
    tag:list[constr(max_length=255)]

@app.post('/admin_create_rec')
async def create_rec_fun(item:new_rec):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    rec_name = item.rec
    rec_dis = item.rec_dis
    rec_key = item.rec_key
    rec_sh_count = item.rec_sh_count
    rec_title = item.rec_title
    domain_name = item.domain
    tag_names = item.tag
    
    #build quary body that return required recommendation
    rec_merging_quary = '''MERGE (s:Suggestion {name: "'''+rec_name+'''",description:"'''+rec_dis+'''",keyword:"'''+rec_key+'''",sh_count:"'''+rec_sh_count+'''",title:"'''+rec_title+'''"})'''
    relation_wdomain_quary = '''MATCH (s:Suggestion {name: "'''+rec_name+'''"}) MATCH (d:Domain {name: "'''+domain_name+'''"}) MERGE (s)- [:IS_LINKED_WITH] ->(d) RETURN s.name,d.name'''
    graph.run(rec_merging_quary)
    relation_result = graph.run(relation_wdomain_quary)
    for tag_name in tag_names:
        relation_wtag_quary = '''MATCH (s:Suggestion {name: "'''+rec_name+'''"}) MATCH (t:Tag {name: "'''+tag_name+'''"}) MERGE (s)- [:IS_LINKED_WITH] ->(t)'''
        graph.run(relation_wtag_quary)

    

    #converting the tabled result to dataframe to extract the reccommendation name from it
    result_pd = pd.DataFrame(relation_result.to_data_frame())

    #make condition in case tag not added sucessfuly return the create recommendation process failed
    if result_pd.empty:
        result_fi = {'tag':'create recommendation process failed'}
    else:
        result_fi = {'tags':list(result_pd['s.name'])[0]+' recommendation added sucessfully and attach to '+list(result_pd['d.name'])[0]+' domain and required tags sucessfully'}

    return result_fi


#api for read required suggestion
class read_rec(BaseModel):
    rec:str
    

@app.post('/admin_read_rec')
async def read_rec_fun(item:read_rec):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    rec_name = item.rec
   
    #build quary body that read the required tag
    quary = '''MATCH (s:Suggestion {name: "'''+rec_name+'''"}) <-[:IS_LINKED_WITH]-> (d:Domain) MATCH (s:Suggestion {name: "'''+rec_name+'''"}) <-[:IS_LINKED_WITH]-> (t:Tag) RETURN s,d,t'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the tag data from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case tag not read sucessfuly return the read tag process failed
    if result_pd.empty:
        result_fi = {'tag':'read recommendation process failed'}
    else:
        result_fi = {'suggestion':result_pd['s'][0],'tag':result_pd['t'],'domain':result_pd['d'][0]}

    return result_fi

#api for update required suggestion
class update_rec(BaseModel):
    rec_old_name:str
    rec_new_name:str
    rec_new_dis:str
    rec_new_key:str
    rec_new_sh_count:str
    rec_new_title:str
    new_related_domain:str
    tag:list[constr(max_length=255)]

@app.post('/admin_update_rec')
async def update_rec_fun(item:update_rec):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    rec_old_name = item.rec_old_name
    rec_new_name = item.rec_new_name
    rec_new_dis = item.rec_new_dis
    rec_new_key = item.rec_new_key
    rec_new_sh_count = item.rec_new_sh_count
    rec_new_title = item.rec_new_title
    new_related_domain = item.new_related_domain
    tag_names = item.tag
   
    #build quary body that update the tag properties and it's relation
    quary = '''MATCH (s:Suggestion {name: "'''+rec_old_name+'''"}) SET s.name = "'''+rec_new_name+'''" , s.description = "'''+rec_new_dis+'''" , s.keyword = "'''+rec_new_key+'''" ,s.sh_count = "'''+rec_new_sh_count+'''", s.title = "'''+rec_new_title+'''" '''
    graph.run(quary)
    
    erase_old_relations_quary = '''MATCH (s:Suggestion {name: "'''+rec_new_name+'''"}) - [r1:IS_LINKED_WITH] -> (d:Domain) MATCH (s:Suggestion {name: "'''+rec_new_name+'''"}) <-[r2:IS_LINKED_WITH]-> (t:Tag) DELETE r1,r2'''
    graph.run(erase_old_relations_quary)
    
    relation_wdomain_quary = '''MATCH (s:Suggestion {name: "'''+rec_new_name+'''"}) MATCH (d:Domain {name: "'''+new_related_domain+'''"}) MERGE (s)- [:IS_LINKED_WITH] ->(d) RETURN s.name,d.name'''
    result = graph.run(relation_wdomain_quary)

    for tag_name in tag_names:
        relation_wtag_quary = '''MATCH (s:Suggestion {name: "'''+rec_new_name+'''"}) MATCH (t:Tag {name: "'''+tag_name+'''"}) MERGE (s)- [:IS_LINKED_WITH] ->(t)'''
        graph.run(relation_wtag_quary)
    
    
    #converting the tabled result to dataframe to extract the tag name from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case suggestion not updated sucessfuly return the update suggestion process failed
    if result_pd.empty:
        result_fi = {'rec':'update suggestion process failed'}
    else:
        result_fi = {'recs':list(result_pd['s.name'])[0]+' tag updated sucessfully and attach to '+list(result_pd['d.name'])[0]+' domain and other required tags sucessfully'}

    return result_fi

#api for delete required suggestion
class delete_rec(BaseModel):
    rec:str

@app.post('/admin_delete_rec')
async def delete_rec_fun(item:delete_rec):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    rec_name = item.rec

    #build quary body detach and delete the required tag
    quary = '''MATCH (s:Suggestion {name: "'''+rec_name+'''"}) DETACH DELETE s'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the tag name from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case tag not deleted sucessfuly return the delete tag process failed (result must be empty)
    if result_pd.empty:
        result_fi = {'recs':'Required suggestion deleted sucessfully'}
    else:
        result_fi = {'recs':'delete suggestion process failed'}

    return result_fi

# Admin apis : Use case 3
#api to create multiple suggestions in one time
class multi_rec(BaseModel):
    recs:list[list[constr(max_length=255)]]
    #the connected tags in list of list with same order of created suggestions in recs
    connected_tags:list[list[constr(max_length=255)]]

@app.post('/admin_create_multi_recs')
async def create_multi_rec_fun(item:multi_rec):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    recs = item.recs
    connected_tags = item.connected_tags

    
    #build quary body that return all required reccommendations
    count = 0
    for rec in recs:
        rec_merging_quary = '''MERGE (s:Suggestion {name: "'''+rec[0]+'''",description:"'''+rec[1]+'''",keyword:"'''+rec[2]+'''",sh_count:"'''+rec[3]+'''",title:"'''+rec[4]+'''"})'''
        graph.run(rec_merging_quary)
        
        relation_wdomain_quary = '''MATCH (s:Suggestion {name: "'''+rec[0]+'''"}) MATCH (d:Domain {name: "'''+rec[5]+'''"}) MERGE (s)- [:IS_LINKED_WITH] ->(d) RETURN s.name,d.name'''
        
        result = graph.run(relation_wdomain_quary)

        for tag_name in connected_tags[count]:
            relation_wtag_quary = '''MATCH (s:Suggestion {name: "'''+rec[0]+'''"}) MATCH (t:Tag {name: "'''+tag_name+'''"}) MERGE (s)- [:IS_LINKED_WITH] ->(t)'''
            graph.run(relation_wtag_quary)
        count +=1
    

    #converting the tabled result to dataframe to extract the reccommendation name from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case the multi recommendation not added sucessfuly return the create recommendation process failed
    if result_pd.empty:
        result_fi = {'rec':'create recommendation process failed'}
    else:
        result_fi = {'recs':list(result_pd['s.name'])[0]+' recommendation added sucessfully' }
    return result_fi

# Admin apis : Use case 4
#Api to update the sh_count when user search about this suggestion
class update_rec_sh_count(BaseModel):
    rec:str
    

@app.post('/increasing_rec_searching_count')
async def increase_sh_count_fun(item:update_rec_sh_count):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    rec_name = item.rec
   
    #build quary body that read the required tag
    quary = '''MATCH (s:Suggestion {name: "'''+rec_name+'''"})  RETURN s.sh_count'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the recommendation sh_count from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #reading the current sh_count and increaing 1 when used/searched by the user
    count = int(result_pd['s.sh_count'][0])
    count += 1
    quary = '''MATCH (s:Suggestion {name: "'''+rec_name+'''"}) SET s.sh_count = "'''+str(count)+'''"  RETURN s.name,s.sh_count'''
    result = graph.run(quary)
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case tag not update sucessfuly return the update sh_count process failed
    if result_pd.empty:
        result_fi = {'rec':'updating the sh_count for this suggestion failed'}
    else:
        result_fi = {'rec':'the sh_count for suggestion '+result_pd['s.name'][0]+' is increased to be '+result_pd['s.sh_count'][0]}

    return result_fi

#Api to track wich suggestions are most searched by user
class read_top_rec(BaseModel):
    n_sugg:str

@app.post('/get_top_n_searched_suggestions')
async def get_top_searched_recs(item:read_top_rec):
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    n_sugg = item.n_sugg
   
    #build quary body that read the required tag
    quary = '''MATCH (n:Suggestion) WITH n,toInteger(n.sh_count) AS ser_count ORDER BY ser_count DESC RETURN n,ser_count LIMIT '''+ n_sugg 
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the recommendation sh_count from it
    result_pd = pd.DataFrame(result.to_data_frame())

    #make condition in case tag not update sucessfuly return the update sh_count process failed
    if result_pd.empty:
        result_fi = {'rec':'reading the sh_count for this suggestion failed'}
    else:
        x=0
        result_fi = {}
        for index,sug in result_pd.iterrows():
            result_fi['suggestion '+str(x)]=sug['n']
            result_fi['seggestion '+str(x)+' searched count']=sug['ser_count']
            x+=1
        # result_fi = {'suggestion':result_pd['n'],'tag':result_pd['t'],'domain':result_pd['d'][0]}

    return result_fi

#Use case 5 : Api to get the data frame for suggestions
# api to export the neo4j data to .csv file? as below
# - each row will consist of
# + suggestion detail ( id , name, title, keywords, description)
# + domain ( name or id)
# + list of tags


@app.get('/get_suggestions_csv')
async def recs_csv():
    #authorization to connect with neo4j graph database
    graph = Graph('neo4j+s://ed887860.databases.neo4j.io:7687', auth=('neo4j','yulO-mLLrt72cJ39FI12Lo-Lr6wtv6qx2oIzUNDl5Zo'))

    # rec_name = item.rec
   
    #build quary body that read the required tag
    quary = '''MATCH (sugg:Suggestion) <-[:IS_LINKED_WITH]-> (domain:Domain) MATCH (sugg:Suggestion) <-[:IS_LINKED_WITH]-> (tag:Tag) 
            WITH sugg,domain, collect(tag.name) as tag_list
            RETURN ID(sugg),sugg.name,sugg.title,sugg.keywords,sugg.description,domain.name,tag_list'''
    result = graph.run(quary)

    #converting the tabled result to dataframe to extract the tag data from it
    result_pd = pd.DataFrame(result.to_data_frame())
    csv_data = result_pd.to_csv()

    #make condition in case tag not read sucessfuly return the read tag process failed
    if result_pd.empty:
        result_fi = {'tag':'read recommendation process failed'}
    else:
        result_fi = {'suggestions':csv_data}

    return result_fi

