import pandas as pd
import requests
import json

keywords = pd.read_csv('C:/Users/david/OneDrive/Documenti/Tirocinio/KeyWords_Da_Analizzare_Conteggio.csv', delimiter = ';')

key_list = {}
#creo un dictionary del tipo "doi":"keyword concatenate"
for index, row in keywords.iloc[1:2].iterrows():
    #if and (keywords.iat[index,0] in social_network) :
    key_list[keywords.iat[index,0]] = ""
    #itero su tutte le colonne della riga tranne la prima (cioè il testo)
    for column in (keywords.iloc[:, 1:].columns):
        #quando trovo un nan lo elimino (il nan è di tipo float)
        if(type(row[column]) != float):
            # i caratteri dopo l'ultimo spazio rappresentano il numero di occorrenze della parola
            indice_spazio = row[column].rfind(' ')
            occorrenze = row[column][indice_spazio:]
            for i in range(int(occorrenze)):
                key_list[keywords.iat[index,0]] += f'{row[column][:indice_spazio]} '
                

#mano a mano che catalogo i documenti sostituisco le keyword con i risultati della catalogazione 
for elem in key_list:
    testo_catalogato = requests.get('https://api.dandelion.eu/datatxt/cl/v1', 
                                    params = {'token': '', 'text':f'{key_list[elem]}', 
                                              'model':str(modello_corrente)})
    key_list[elem] = testo_catalogato.json()
    

try:
    for elem in key_list:
        lista = []
        for ambito in key_list[elem]['categories']:
            if ambito['score']>0.4:
                lista.append(f"{ambito['name']}    ({ambito['score']})")
        dataframe1 = dataframe1.append(pd.DataFrame([lista], index=[elem]))
except:
    pass


dataframe1.to_csv(r"C:/Users/david/OneDrive/Documenti/Tirocinio/TotalTextClassified_More5.csv",encoding = "utf_8", sep = ';',index=True)
