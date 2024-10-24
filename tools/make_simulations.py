from datetime import datetime
import csv
import json
import pymysql
import sys
import pandas as pd
import random
import numpy as np
import h5py
import os.path

def read_csv(filename:str)->str:
    with open(filename, encoding="utf-8") as csvf:
        csv_reader=csv.DictReader(csvf)
        json_array=[r for r in csv_reader]
    return json.dumps(json_array, force_ascii=False)

def get_db(db_name:str, autocommit:bool = True)->pymysql.connect:
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
                user="cenarios_macro",
                passwd="123123",
                charset='utf8mb4',
                database=db_name,
                autocommit=autocommit,
                cursorclass=pymysql.cursors.DictCursor)         # type: ignore
        return mydb
    except:
        raise


def cria_projecao(db, filename, nome_projecao, data_projecao):
    
    crsr=db.cursor()
    select_stmt = "DELETE FROM projecoes WHERE nome_projecao = '"+nome_projecao+"';"
    crsr.execute(select_stmt)

    matriz_covarianca=pd.read_excel(filename,sheet_name="Covarianca_real")
    matriz_covarianca=matriz_covarianca.set_index(matriz_covarianca.columns[0])
    matriz_covarianca.index.name=None
    select_stmt = "INSERT INTO projecoes VALUES(NULL, '"+nome_projecao+"','"+data_projecao+"','"+matriz_covarianca.to_json(force_ascii=False)+"',0,0) "
    crsr.execute(select_stmt)

    matriz_covarianca=pd.read_excel(filename,sheet_name="Covarianca_nominal")
    matriz_covarianca=matriz_covarianca.set_index(matriz_covarianca.columns[0])
    matriz_covarianca.index.name=None
    select_stmt = "INSERT INTO projecoes VALUES(NULL, '"+nome_projecao+"','"+data_projecao+"','"+matriz_covarianca.to_json(force_ascii=False)+"',1,0) "
    crsr.execute(select_stmt)



def load_esperados(nome_projecao: str, nome_cenario:str, probabilidade: float, ret_dict:dict, db:pymysql.connect):
    sql="INSERT INTO retornos_esperados (nome_projecao, nome_cenario, probabilidade_cenario, retornos_esperados) VALUES ('"
    sql+=nome_projecao+"','"+nome_cenario+"',"+str(probabilidade)+",'"+json.dumps(ret_dict,ensure_ascii=False)+"');"
    crsr=db.cursor()
    crsr.execute(sql)
    return

def insert_esperados(db, nome_projecao, cenarios):
    sql="SELECT ID, nominal FROM projecoes WHERE nome_projecao='"+nome_projecao+"';"
    crsr=db.cursor()
    crsr.execute(sql)
    rows = crsr.fetchall()
    id_real=str(rows[0]["ID"]) if rows[0]["nominal"]==b'\x00' else str(rows[1]["ID"])
    id_nominal=str(rows[0]["ID"]) if rows[0]["nominal"]==b'\x01' else str(rows[1]["ID"])

    select_stmt = "DELETE FROM retornos_esperados WHERE ID_projecao='"+id_real+"' OR ID_projecao='"+id_nominal+"';"
    crsr=db.cursor()
    crsr.execute(select_stmt)

    for c in cenarios.columns:
        retornos_esperados_reais=(cenarios[c][2:]/12).to_dict()
        retornos_esperados_nominais=((cenarios[c][2:]+cenarios[c][1])/12).to_dict()
        sql="INSERT INTO retornos_esperados VALUES (NULL,"+id_real+",'"+c+"',"+str(cenarios[c][0])+",'"+json.dumps(retornos_esperados_reais, ensure_ascii=False)+"');"
        crsr.execute(sql)
        sql="INSERT INTO retornos_esperados VALUES (NULL,"+id_nominal+",'"+c+"',"+str(cenarios[c][0])+",'"+json.dumps(retornos_esperados_nominais, ensure_ascii=False)+"');"
        crsr.execute(sql)

    return sql


db=get_db("cenarios_macro")
nome_projecao=input("Nome da projeção (deixar em branco para criar nova): ")
while nome_projecao=="":
    nome_projecao=input("Nome da nova projeção: ")
    data_projecao=datetime.now().strftime("%Y-%m-%d")

    cria_projecao(db, "History_20170930_20220930.xlsx", nome_projecao, data_projecao)
    cenarios=pd.read_excel("History_20170930_20220930.xlsx",sheet_name="Cenarios")
    cenarios=cenarios.set_index("Unnamed: 0")
    cenarios.index.name=None

    insert_esperados(db, nome_projecao, cenarios)


crsr=db.cursor()
sql="SELECT matriz_covarianca, nominal, ID FROM projecoes WHERE nome_projecao='"+nome_projecao+"';"
crsr.execute(sql)
rows = crsr.fetchall()
for row in rows:
    if row["nominal"]==b'\x00':
        print("Retornos reais")
    else:
        print("Retornos nominais")

    cov_matrix=pd.read_json(row["matriz_covarianca"])
    sql="SELECT nome_cenario, probabilidade_cenario, retornos_esperados FROM retornos_esperados WHERE ID_projecao='"+str(row["ID"])+"';"
    crsr.execute(sql)
    rows = crsr.fetchall()
    rets=pd.read_json("["+rows[0]["retornos_esperados"]+"]")   #ensure_ascii=False
    for r in rows[1:]:
        x=pd.read_json("["+r["retornos_esperados"]+"]")
        rets=pd.concat([rets,x],axis=0)

    probs=[float(x["probabilidade_cenario"]) for x in rows]
    rets.index=[x["nome_cenario"] for x in rows]    #type: ignore

    sim_months=600 #int(sys.argv[2])
    number_of_simulations=10000 #int(sys.argv[3])
    simulations=[]

    # Make all simulations equal

    random.seed(10)
    r = np.random.RandomState(1234)

    idx=random.choices(rets.index,weights=probs, k=number_of_simulations)
    recs=[]
    for z in range(0,number_of_simulations):
        x = r.multivariate_normal(rets.loc[idx[z]],cov_matrix,sim_months).T  #1st set of returns
        d={cov_matrix.index[i]:x[i].tolist() for i in range(0,len(x))}
        recs.append(x)
        if z%500==0:
            print("Sim: ",z)
    print("Salvando .hdf5...")

    recs=np.array(recs)
    if row["nominal"]==b'\x01':
        filename=nome_projecao+"_nominal"+".hdf5"
    else:
        filename=nome_projecao+".hdf5"

    f = h5py.File(os.path.join("..","etrnty_investimentos","etrnty_investimentos","atuario", "forecasts",filename), "w")
    dset = f.create_dataset("data", data=recs)
    dset.flush()
    dset = f.create_dataset("index",data=list(rets.columns))
    dset.flush()
    print("Done!")
sys.exit(0)