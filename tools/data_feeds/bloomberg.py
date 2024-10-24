from sqlalchemy import create_engine, types
from et_lib.ET_Data_Reader import BloombergHistoricalData;
from economatica import engine, mysql_replace_into, Ativo
from datetime import datetime
import pandas as pd
import logging
import sys
import os

tickers=["SPBDUB3T Index",
         "HFRXGL Index",
         "LBUSTRUU Index",
         "NDDUWI Index",
         "CPURNSA Index"]

if __name__=="__main__":
    logger = logging.getLogger("bloomberg")
    logger.setLevel(level=logging.INFO)
    logStreamFormatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s" )
    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    consoleHandler.setFormatter(logStreamFormatter)
    consoleHandler.setLevel(level=logging.INFO)
    fileHandler = logging.FileHandler(encoding="utf-8", filename=os.path.join("data_feeds","bloomberg.log"))
    fileHandler.setFormatter(logStreamFormatter)
    fileHandler.setLevel(level=logging.INFO)
    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)

    startDate=datetime.strptime("1979-12-31","%Y-%m-%d")
    endDate=datetime.today()
    cols=[]
    for t in tickers:
        try:
            a=Ativo(t,"bloomberg")
        except LookupError as e:
            logger.warning(e.args[0])
            continue
        cols.append(a.cod_ativo)

    bb=BloombergHistoricalData(startDate, endDate, tickers, ["PX_LAST"], periodicity="MONTHLY")
    df=bb.getData().droplevel(level=1,axis=1)
    df.columns=cols
    df.index.name="Data"
    df=df.dropna()

    with engine.begin() as connection:
        x=[]
        for c in df.columns:
            x+=[{"data":d, "cod_campo":"preço", "valor":df[c].loc[d], "cod_ativo":c} for d in df.index]

        idf=pd.DataFrame(data=x)
        idf.to_sql('historico', con=connection, if_exists='append',index=False, dtype={"data":types.Date,"cod_campo":types.Text,"valor":types.Float,"cod_ativo":types.Text}, method=mysql_replace_into)
        logger.info("Imported: "+str(cols))