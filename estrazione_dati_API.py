import pymysql
import requests
import json
import re
from bs4 import BeautifulSoup

# connessione database
connection = pymysql.connect(host="localhost",user="root",passwd="",database="tirocinio 2" )
cursor = connection.cursor()
        
    
# pagine con pochi link => tempi piu lunghi
x=1
url_API = 'https://zenodo.org/api/records'
while(x<100):
    response = requests.get(url_API, params={
                'q': '("covid") OR ("covid-19") OR
                ("sars-cov-2") OR ("sars cov 2")',
                'access_token':'valore_token',
                'type':'dataset',
                'size':800,
                'page':x,
                'sort': 'mostrecent'})
    
    x+=1
    
    # scansione terminata
    if(response.status_code == 400):
        print("Fine elementi")
        break

    # intercetto tutti gli errori che non sono 400 
    if(response.status_code != 200):
        print("Scansione terminata con errore")
        break
        
    # estraggo il json
    json=response.json()

    # vettore contenente i dati delle pubblicazioni 
    hits=json["hits"]["hits"]
    
    for diz in hits:
        
        meta=diz["metadata"]
        
        
        # estrai_pubb 
        try:
            doi=diz["doi"] 
        except:
            doi="" 
        try:
            title=str(meta["title"].replace('"', '').replace('\n', ''))
        except:
            title=""   
            
        try:
            language=meta["language"]
        except:
            language=""
            
        # warning se le note sono costituite da un indirizzo web
        try:
            notes_html=meta["notes"]   
            notes=str((BeautifulSoup(notes_html, 'html.parser')).text.replace('"', '').replace('\n', ''))
        except:
            notes=""
    
        try:
            description_html=meta["description"] 
            description=str((BeautifulSoup(description_html, 'html.parser')).text.replace('"', '').replace('\n', ''))
        except:
            description=""
    
            
        
        try:
            license=meta["license"]["id"]    
        except:
            license="no license"
            
        try:
            access_right=meta["access_right"]  
        except:
            access_right=""
            
            
        try:
            access_right_category=meta["access_right_category"]  
        except:
            access_right_category=""
            
        try:
            access_conditions_html=meta["access_conditions"]  
            access_conditions=str((BeautifulSoup(access_conditions_html, 'html.parser')).text.replace('"', '').replace('\n', ''))
        except:
            access_conditions=""
            
        try:
            method_html=meta["method"] 
            method=str((BeautifulSoup(method_html, 'html.parser')).text.replace('"', '').replace('\n', ''))
        except:
            method=""
    
        try:
            created=diz["created"]   
        except:
            created=""
    
        try:
            updated=diz["updated"]    
        except:
            updated=""
            
        try:
            volume=diz["stats"]["volume"]    
        except:
            volume=""
    
        try:
            # inserisco le pubblicazioni nel database
            query_pubb = "INSERT INTO pubblicazione(doi,title,language,notes,description,method,license,access_right,access_right_category,access_conditions,created,updated,volume) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            args_pubb = (doi,title,language,notes,description,method,license,access_right,access_right_category,access_conditions,created,updated,volume)
            cursor.execute(query_pubb, args_pubb)
        except Exception:
                pass
            
        
        
        
        
        # estrai_file 
        try:
            files=diz["files"]
        except:
            files=""
    
        for file in files: 
        
            try:
                link_f=file["links"]["self"]
            except:
                link_f=""
                
            try:
                key_f=file["key"]
            except:
                key_f=""
    
            try:
                type_f=file["type"]
            except:
                type_f=""   
    
            try:
                size=file["size"] #in byte
            except:
                size="" 
              
            
        
            try:
                # inserisco i file nel database
                query_file = "INSERT INTO file(link,key_f,type,size,pubblicazione) VALUES (%s,%s,%s,%s,%s)"
                args_file = (link_f,key_f,type_f,size,doi)
                cursor.execute(query_file, args_file)
            except Exception:
                pass
            
           
    
    
    
            
        # estrai_key 
        try:
            key_words=meta["keywords"]
        except:
            key_words=""
    
        for keyword in key_words:    
            # alcune pubblicazioni hanno keyword scritte nella stessa riga e separate con "," o ";" anziche sotto forma di array
            for elem in re.split('; |,',keyword):            
                try:
                    # inserisco le keyword nel database
                    query_key = "INSERT INTO keyword(keyword) VALUES (%s)"
                    args_key = str((elem.replace('"', '').replace('\n', '')))
                    cursor.execute(query_key, args_key)
                except Exception:
                    pass

                try:
                    # query relativa alle pubblicazioni-key (riferimento)
                    query_rif = "INSERT INTO riferimento(pubblicazione,keyword) VALUES (%s,%s)"
                    args_rif = (doi,elem)
                    cursor.execute(query_rif, args_rif)
                except Exception:
                    pass
    
    
    
        
        
        
        
        # estrai_ric
        try:
            creators=meta["creators"]
        except:
            creators=""
    
        for creator in creators:  
                
            try:
                name=creator["name"]
            except:
                name=""

            try:
                affiliation=str(creator["affiliation"].replace('"', '').replace('\n', ''))
            except:
                affiliation=""
                
            try:
                id=creator["orcid"]
            except:
                id=hash(name+affiliation) 

            try:  
                # inserisco i ricercatori nel database
                query_ric = "INSERT INTO ricercatore(id,name,affiliation) VALUES (%s,%s,%s)"
                args_ric = (id,name,affiliation)
                cursor.execute(query_ric, args_ric)
            except Exception:
                pass     

            try:  
                # query relativa alle pubblicazioni-ricercatori (caricamento)
                query_car = "INSERT INTO caricamento(pubblicazione,ricercatore) VALUES (%s,%s)"
                args_car = (doi,id)
                cursor.execute(query_car, args_car)
            except Exception:
                pass  
            


connection.commit()
connection.close()
