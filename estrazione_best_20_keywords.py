import pandas as pd
import pymysql
import collections

#connessione database
connection = pymysql.connect(host="localhost",user="root",passwd="",database="tirocinio_keyword3" )
cursor = connection.cursor()

cursor.execute("set @num := 0;")
cursor.execute("set @type := '' COLLATE utf8mb4_unicode_ci;")
cursor.execute("""select `text`,`keyword`,`numero`,`TFIDF`, row_number
from (
   select `text`,`keyword`,`numero`,`TFIDF`, @num := if(@type = text, @num + 1, 1) as row_number, @type := text as dummy
  from pubblicazione
  order by `text`,`TFIDF` DESC
) as x where x.row_number <= 20
""")

rows = cursor.fetchall()


dict_keyword = collections.defaultdict(list)

dataframe = pd.DataFrame()


for pubb in rows:
    dict_keyword[pubb[0]].append(f"{pubb[1]} {str(pubb[2])}")


for key,value in dict_keyword.items():
    list_keyword = pd.DataFrame([value], index = [key])
    dataframe = dataframe.append(list_keyword)
    
    
dataframe.to_csv(r"C:/Users/david/OneDrive/Documenti/Tirocinio/KeyWords_Da_Analizzare_Conteggio.csv",encoding = "utf_8", sep = ';',index=True)

