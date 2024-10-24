import pymysql
from pymysql import cursors
import os
from datetime import datetime

def get_db(db_name:str, autocommit:bool = True)->pymysql.Connection:
    """Opens a connection to a database on the Etrnty server

        Args:
            db_name : database name on server
            autocommit (bool) : Tells if changes will be commited automatically default is True or if connect.commit() must be called

        Raises:
            None

        Returns:
            a pymysql.connect object with the open database connection"""

    host = "172.16.215.2"
    #host="201.6.114.229"
    
    try:
        mydb = pymysql.connect(
                host=host,
                user="root",
                passwd="Loadstep1!",
                charset='utf8mb4',
                database=db_name,
                autocommit=autocommit,
                cursorclass=pymysql.cursors.DictCursor)         # type: ignore
        return mydb
    except:
        raise

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def get_file_from_db(id:int)->dict:
    """
    return dict:{"filename":str, "mimetype": str, "file":binary}
    """
    db=get_db("estrela_vespertina")
    cursor=db.cursor()
    sql="SELECT filename,mimetype, file FROM files WHERE ID="+str(id)+";"
    cursor.execute(sql)
    r=cursor.fetchone()
    db.close
    return r
    
if __name__ =='__main__':
    db=get_db("estrela_vespertina")
    cursor=db.cursor()
    input("Coloque todos os arquivos no diretorio files_to_upload e pressione enter")
    arr = os.listdir("files_to_upload")
    for a in arr:
        print("Detalhes do arquivo: "+a)
        CNPJ=input("CNPJ da gestorta: ")
        tabela_referencia=input("Tabela de referência (reunioes, deligence_gestora): ")
        ID_referencia=input("ID de referencia: ")
        titulo=input("Titulo: ")
        mime=input("Mime (application/pdf): ")
        mime = mime if mime!="" else 'application/pdf'
        data=input("Data ("+datetime.now().strftime("%Y-%m-%d")+"): ")
        data = data if data !="" else datetime.now().strftime("%Y-%m-%d")

        s = convertToBinaryData(os.path.join("files_to_upload",a))
        sql = """INSERT INTO files ( CNPJ_gestora, tabela_referencia, ID_referencia, `Data`, Description, mimetype, filename, file) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
        v_tuple=(CNPJ, tabela_referencia ,ID_referencia ,data,titulo,mime,a,s)
        r=cursor.execute(sql,v_tuple)

        print("Arquivo inserido com ID: ", cursor.lastrowid)
        print('<a href="/estrela_vespertina/download?ID='+str(cursor.lastrowid)+'">'+titulo+'</a>')
        print()

    print("done")