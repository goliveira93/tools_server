from etrnty_investimentos.estrela_vespertina.db_functions import get_db

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
    path="C:/Users/mbrisac/ETRNTY Capital Planejadora Financeira/Rede ETRNTY - Documentos/Due Dilligence/Encore/"
    filename="Relatório de Gerenciamento de Risco - 09-02-2022.pdf"
    titulo="Relatório de risco"
    tabela="diligence_gestora" #"reunioes"
    ID=16
    s = convertToBinaryData(path+filename)
    db=get_db("estrela_vespertina")
    cursor=db.cursor()
    sql = """INSERT INTO files ( CNPJ_gestora, tabela_referencia, ID_referencia, `Data`, Description, mimetype, filename, file) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
    v_tuple=("22.688.191/0001-69", tabela,str(ID) ,"2022-09-26",titulo,'application/pdf',filename,s)
    r=cursor.execute(sql,v_tuple)
    print("done")