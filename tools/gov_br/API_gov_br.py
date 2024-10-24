import requests
from pprint import pprint
import pickle
import pandas as pd
import sys

#Swagger: https://api.portaldatransparencia.gov.br/swagger-ui.html

gov_plano_orcamentario = 'https://api.portaldatransparencia.gov.br/api-de-dados/despesas/plano-orcamentario' 


my_header = {
    "chave-api-dados": '39dd80063ec039504e573633d0576630'
}



def read_year(year:int,page:int=1)->pd.DataFrame:
    params = {
                "ano":str(year),
                "pagina":str(page)
            }

    resp = requests.get(url=gov_plano_orcamentario, params=params,headers=my_header)
    data=[]
    while resp.status_code==200 and page<5000 and len(resp.json())>0:
        print(page)
        for x in resp.json():
            data.append(x)
    
        page+=1
        params["pagina"]=str(page)
        resp = requests.get(url=gov_plano_orcamentario, params=params,headers=my_header)

    df=pd.DataFrame(data)
    return df

df=read_year(2021)

df.to_excel("despesas_2021.xlsx")


