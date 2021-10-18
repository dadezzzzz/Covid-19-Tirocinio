#lemmatizer + calcolo TF*IDF (solo inglese) modello più lento ma più accurato per le NER

import nltk
from nltk import word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
import pandas as pd
import re
import en_core_web_trf
import pymysql



#connessione database
connection = pymysql.connect(host="localhost",user="root",passwd="",database="tirocinio 1" )
cursor = connection.cursor()

extract = "select doi,title,description from pubblicazione where language_detected ='en'"
cursor.execute(extract)
rows = cursor.fetchall()
connection.close()



#dizionario che mappa gli attributi che iniziano con j associando il carattere di riferimento per gli aggettivi in wordnet
#faccio lo stesso per nomi(n), avverbi(r) e verbi(v)
tag_map = {"j": wordnet.ADJ,
           "n": wordnet.NOUN,
           "v": wordnet.VERB,
           "r": wordnet.ADV}

lemmatizer = WordNetLemmatizer()


#creo una lista vuota in cui inserirò i documenti lemmizzati
documents_list = []

#modello per le ner
nlp = en_core_web_trf.load()

for text in rows:
    # creo una lista vuota in cui inserirò i lemmi
    word_list = []   
    
    # dividiamo il testo in token (text[1] è il titolo, text[2] è la descrizione)
    descr_title = text[1]+'. '+text[2]
    
    # eliminazione di link, simboli e lettere non inglesi
    text_no_link = re.sub(r'\S*(http|https)://\S+','',descr_title, 0, re.MULTILINE | re.IGNORECASE)
    text_no_link_email_ = re.sub(r'[.\-<>,∆≤~=_/\'\"\\:+\*\(\)\[\]\{\}]',' ',text_no_link, 0, re.MULTILINE | re.IGNORECASE)
    text_no_link_symbols = re.sub(r'\S*[^a-zA-Z0-9 ]\S*','',text_no_link_email_, 0, re.MULTILINE | re.IGNORECASE)
    
    #elimino stringhe contenenti 3 o più numeri di seguito
    text_no_link_email_num = re.sub(r'\S*\d{3,}\S*','',text_no_link_symbols, 0, re.MULTILINE | re.IGNORECASE)
    
    # eliminazione di parole contenenti lettere ripetute più di 3 volte
    text_no_link_email_rip_num = re.sub(r'\S*(.)\1{2,}\S*','',text_no_link_email_num, 0, re.MULTILINE | re.IGNORECASE)
    

    
    #elimino i termini che indicano ner 
    doc = nlp(text_no_link_email_rip_num)
    for chunk in doc.ents:
        if ( chunk.label_ != "WORK_OF_ART"):
            #print(chunk, f'({chunk.label_})')
            #elimino le ner, tranne per woa perché elimina intere frasi che possono interessarci
            text_no_link_email_rip_num = re.sub(r''+chunk.text, '', text_no_link_email_rip_num)   
            
    #trasformo in token (lista di parole)
    token = word_tokenize(text_no_link_email_rip_num)
    
    #partendo da una lista di parole creiamo una lista di tuple con formato (parola,tag_nltk)
    token_tags = nltk.pos_tag(token)
     
    
    #per ogni elemento della lista cambiamo il valore del tag adattandolo alla codifica wordnet
    for elem_tag in token_tags:
        #estraggo il primo carattere del secondo elemento della tupla, poi mappo tale valore sfruttando il dizionario tag_map
        wordnet_tag = tag_map.get(elem_tag[1][0].lower())
        #alcuni tag nltk non esistono in wordnet quindi la nostra mappatura restituisce "none" cioè non ci interessano
        #(ad esempio numeri, punteggiatura, pronomi, connettivi etc etc), eliminiamo anche le parole a singola lettera/carattere
        if (wordnet_tag != None):
            #print(elem_tag,wordnet_tag)
            #applico il lemmatizing(dopo aver convertito a lettere piccole altrimenti il lemmatize
            #non funziona) ed aggiungo nella lista di lemmi se la parola ha più di 1 carattere
            lemma = lemmatizer.lemmatize(elem_tag[0].lower(), pos=wordnet_tag)
            if(len(lemma)>1):
                word_list.append(lemma)

    
    
    #aggiungo alla lista di documenti (che a loro volta sono liste di token)
    documents_list.append(word_list)  

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

#creo la matrice densa che contiene i TF-IDF ed il conteggio delle occorrenze 
def dummy_fun(doc):
    return doc

tfIdfVectorizer = TfidfVectorizer(
    #stop_words=stop_words,
    min_df=2,
    max_df=0.75,
    analyzer='word',
    tokenizer=dummy_fun,
    preprocessor=dummy_fun,
    token_pattern=None)

cv = CountVectorizer(
    #stop_words=stop_words,
    min_df=2,
    max_df=0.75,
    tokenizer=dummy_fun,
    preprocessor=dummy_fun,
    token_pattern=None)


TfidfVectorizer = tfIdfVectorizer.fit(documents_list)  
CountVectorize = cv.fit(documents_list)

i = 0
dataframe_count = pd.DataFrame()
dataframe_tfidf = pd.DataFrame()

for doc in documents_list:  
    v_2 = CountVectorize.transform([doc])
    tfIdf = tfIdfVectorizer.transform([doc])
    
    for elem in tfIdf:
        #trasformo in una matrice densa inserendo le parole come colonne e il doi come indice 
        TF_IDF_Matrix = pd.DataFrame(elem.todense(), columns=TfidfVectorizer.get_feature_names(), index = [rows[i][0]])
        dataframe_tfidf = dataframe_tfidf.append(TF_IDF_Matrix)
        

    for elem in v_2:
        #trasformo in una matrice densa inserendo le parole come colonne e il doi come indice 
        COUNT_Matrix = pd.DataFrame(elem.todense(), columns=CountVectorize.get_feature_names(), index = [rows[i][0]])
        dataframe_count = dataframe_count.append(COUNT_Matrix)
        i+=1
        
#per ogni elemento della matrice di TF-IDF inserisco la parola nel DB inserendo anche il numero di occorrenze (se TF-IDF>0.1)
connection = pymysql.connect(host="localhost",user="root",passwd="",database="tirocinio_keyword3" )
cursor = connection.cursor()

#resetto tutti i dati nella tabella
sql = "DELETE FROM `pubblicazione`"
cursor.execute(sql)
connection.commit()

#itero su tutte le righe: row -> riga completa, index -> indice della riga
for indexR, row in dataframe_tfidf.iterrows():
    #itero su tutte le colonne della riga
    for column in (dataframe_tfidf.columns):
        TFIDF = float(row[column])
        if(TFIDF>0.1):
            query_pubb = "INSERT INTO pubblicazione(text,keyword,numero,TFIDF) VALUES (%s,%s,%s,%s)"
            args_pubb = (str(indexR),str(column),dataframe_count[column][indexR],TFIDF)
            cursor.execute(query_pubb, args_pubb)
            
connection.commit()
connection.close()
