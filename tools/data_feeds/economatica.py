from ftplib import FTP
import os
import pandas as pd
import pymysql
import re
import logging
import sys
from sqlalchemy import create_engine, types

engine = create_engine("mysql+mysqldb://precos:123123@172.16.215.2/precos")

def get_db(autocommit:bool = True)->pymysql.connect:
    """Opens a connection to a database on the Etrnty server

        Args:
            db_name : database name on server
            autocommit (bool) : Tells if changes will be commited automatically default is True or if connect.commit() must be called

        Raises:
            None

        Returns:
            a pymysql.connect object with the open database connection"""

    host = "172.16.215.2"
    
    try:
        mydb = pymysql.connect(
                host=host,
                user="precos",
                passwd="123123",
                charset='utf8mb4',
                database="precos",
                autocommit=autocommit,
                cursorclass=pymysql.cursors.DictCursor)         # type: ignore
        return mydb
    except:
        raise



class Ativo:

    def __init__(self, cod_ativo:str, tipo_identificador:str|None=None):
        """
        propriedades:
        cod_ativo: str          - código Etrnty para o ativo
        identificadores: dict   - list(dict(tipo_identificador, identificador)) com todos os identificadores conhecidos 
        """
        self.db=get_db()
        self.cod_ativo=self.db_get_cod_ativo(cod_ativo, tipo_identificador) if tipo_identificador is not None else cod_ativo
        self.identificadores = self.db_get_identificadores(self.cod_ativo)

    def db_get_cod_ativo(self, identificador:str, cod_identificador:str)->str:
        """Retorna o código identificador Etrnty para um ativo, dado o seu código em qualquer outro identificador
           raise: LookupError se o ativo não for encontrado
        """
        sql="SELECT cod_ativo FROM ativo_identificadores WHERE cod_identificador='"+cod_identificador+"' AND identificador='"+identificador+"';"
        crsr=self.db.cursor()
        crsr.execute(sql)
        cod_ativo=crsr.fetchone()
        if cod_ativo is None:
            raise LookupError("LookupError: ("+str(identificador)+","+str(cod_identificador)+")",identificador, cod_identificador)
        else:
            return cod_ativo["cod_ativo"]
    
    def db_get_identificadores(self, cod_ativo:str)->list[dict]:
        sql = "SELECT cod_identificador, identificador FROM ativo_identificadores WHERE cod_ativo='"+cod_ativo+"';"
        crsr=self.db.cursor()
        crsr.execute(sql)
        ident_list=crsr.fetchall()
        return [{i["cod_identificador"]:i["identificador"]} for i in ident_list]


def download_csv():
    curr_dir=os.getcwd()
    os.chdir("data_feeds")
    filename=os.path.join("feed fundos.csv")
    ftp=FTP("datafeed.economatica.com",user='mbrisac@etrnty.com.br',passwd='encfc65' )
    ftp.cwd("feed")
    ftp.retrbinary(f"RETR {filename}", open(filename, "wb").write)
    ftp.quit()
    os.chdir(curr_dir)

def mysql_replace_into(table, conn, keys, data_iter):
    from sqlalchemy.dialects.mysql import insert
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.sql.expression import Insert

    @compiles(Insert)
    def replace_string(insert, compiler, **kw):
        s = compiler.visit_insert(insert, **kw)
        s = s.replace("INSERT INTO", "REPLACE INTO")
        return s

    data = [dict(zip(keys, row)) for row in data_iter]
    conn.execute(table.table.insert(), data)
    #conn.execute(table.table.insert(replace_string=""), data)

#logging.basicConfig(level=logging.INFO, filemode="a", filename=os.path.join("data_feeds","economatica.log"), format="%(asctime)s - %(levelname)s - %(message)s")
if __name__=="__main__":
    logger = logging.getLogger("economatica")
    logger.setLevel(level=logging.INFO)
    logStreamFormatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s" )
    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    consoleHandler.setFormatter(logStreamFormatter)
    consoleHandler.setLevel(level=logging.INFO)
    fileHandler = logging.FileHandler(encoding="utf-8", filename=os.path.join("data_feeds","economatica.log"))
    fileHandler.setFormatter(logStreamFormatter)
    fileHandler.setLevel(level=logging.INFO)
    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)


    download_csv()
    logger.info("Downloaded file from economatica.")

    filename=os.path.join(".","data_feeds","feed fundos.csv")
    df=pd.read_csv(filename,  encoding='latin-1', encoding_errors='replace')

    df['Ativo'] = df['Ativo'].apply(lambda x: re.sub("<.*>", "", x))
    df=df[df.columns[0:4]]
    
    with engine.begin() as connection:
        for i in (df["Ativo"].unique()):
            idf=df.loc[df["Ativo"]==i]
            idf=idf.drop(columns=["Ativo"])
            idf=idf.set_index("Data")
            idf.columns=["preço","patrimônio"] #type:ignore

            x=[]
            for c in idf.columns:
                x+=[{"data":d, "cod_campo":c, "valor":idf[c][d]} for d in idf.index]

            try:
                a=Ativo(i,"economática")
            except LookupError as e:
                logger.warning(e.args[0])
                continue
            
            idf=pd.DataFrame(data=x)
            idf["cod_ativo"]=a.cod_ativo
            idf=idf[idf["valor"]!="-"]
            idf["valor"]=idf["valor"].astype(float)
            idf.to_sql('historico', con=connection, if_exists='append',index=False, dtype={"data":types.Date,"cod_campo":types.Text,"valor":types.Float,"cod_ativo":types.Text}, method=mysql_replace_into) #(table="historico", conn=connection, keys=["data","cod_campo","cod_ativo"]))
            logger.info("Imported: "+a.cod_ativo+" ("+str(idf.shape[0])+") records")