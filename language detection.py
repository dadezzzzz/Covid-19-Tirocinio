import re
import fasttext
import pymysql
import en_core_web_trf


# connessione database
connection = pymysql.connect(host="localhost",user="root",passwd="",database="tirocinio 2" )
cursor = connection.cursor()

# estrazione di chiave,titolo e descrizione dal DB 
extract = "select doi,title,description from pubblicazione limit 10"
cursor.execute(extract)
rows = cursor.fetchall()

# inizializzazione del modello per estrarre la lingua
fmodel = fasttext.load_model('C:/Users/david/OneDrive/Desktop/Tirocinio/programmi/lid.176.bin')

# caricamento del modello per estrarre le NER
nlp = en_core_web_trf.load()

# per ogni riga viene estratta la lingua e viene inserisco nel db
for row in rows:
        
    text = row[1]+'. '+row[2]
     
    # eliminazione di link, mail e simboli 
    text_no_link = re.sub(r'\S*(http|https)://\S+','',text, 0, re.MULTILINE | re.IGNORECASE)
    text_no_link_email = re.sub(r'(\S*[@]\S*)','',text_no_link, 0, re.MULTILINE | re.IGNORECASE)
    text_no_link_email_ = re.sub(r'[.\-<>,~=_/\"\\:+\*\(\)\[\]\{\}]',' ',text_no_link_email, 0, re.MULTILINE | re.IGNORECASE)
    
    # eliminazione di parole contenenti lettere ripetute piu di 3 volte di seguito
    text_no_link_email_rip = re.sub(r'\S*(.)\1{2,}\S*','',text_no_link_email_, 0, re.MULTILINE | re.IGNORECASE)
    
    # eliminazione di stringhe contenenti 4 o piu numeri di seguito
    text_no_link_email_rip_num = re.sub(r'\S*\d{4,}\S*','',text_no_link_email_rip, 0, re.MULTILINE | re.IGNORECASE)
    
    # eliminazione di termini che indicano ner escluse le WORK_OF_ART
    doc = nlp(text_no_link_email_rip_num)
    for chunk in doc.ents:
        if chunk.label_ != "WORK_OF_ART":
            text_no_link_email_rip_num = re.sub(r''+chunk.text, '', text_no_link_email_rip_num)      
    
    # estrazione della lingua 
    language = fmodel.predict(text_no_link_email_rip_num)
    if (language[1][0])>= 0.85:
        update = "UPDATE `pubblicazione` SET `language_detected` = '"+language[0][0][-2:]+"' WHERE `doi` = '"+ row[0]+"'"
    else:
        update = "UPDATE `pubblicazione` SET `language_detected` = 'low confidence' WHERE `doi` = '"+ row[0]+"'" 
        
    cursor.execute(update)

connection.commit()
connection.close()
