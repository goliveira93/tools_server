import pandas as pd
from settings import basket_on, basket_off
from datetime import datetime
from et_lib.ET_Data_Reader import BasketHistoricalData
import plotly.figure_factory as ff
import sys
import  plotly.graph_objects as go
from    plotly.subplots import make_subplots
from scipy.stats import shapiro
import numpy as np
from scipy import stats
import os


def add_qq_fig(dados, fig, title, row):
    st=shapiro(dados)
    X_lognorm = np.random.normal(loc=dados.mean(), scale=dados.std(), size=len(dados))
    qq = stats.probplot(X_lognorm, dist='norm', sparams=(1))
    x = np.array([qq[0][0][0], qq[0][0][-1]])

    if st.pvalue<0.05:
        fig.add_scatter(x=qq[0][0], y=qq[0][1], marker_color="red", mode='markers+text',col=2,row=row, showlegend=False)
        fig.layout.annotations[row*2-1].update(text="NOT SHAPIRO NORMAL")
    else:
        fig.add_scatter(x=qq[0][0], y=qq[0][1], marker_color="green", mode='markers',col=2,row=row, showlegend=False)
    fig.add_scatter(x=x, y=qq[1][1] + qq[1][0]*x, marker_color="gray", mode='lines',col=2,row=row, showlegend=False)
    return fig

def get_historical_returns(startDate:datetime, endDate:datetime, offshore:bool=True)->pd.DataFrame:
    if offshore is True:
        basket=basket_off
        basket.append({"Name":"Deflator","Ticker":"US CPI", "Source":"Database"})
        deflator="US CPI"
    else:
        basket=basket_on
        basket.append({"Name":"Deflator","Ticker":"IPC-A", "Source":"Database"})
        deflator="IPC-A"

    ticker_to_name={i["Ticker"]:i["Name"] for i in basket}
    bb=BasketHistoricalData("Benchmarks",startDate,endDate,basket)
    bb.loadFromDatabase(periodicity="MONTHLY")
    prices=bb.getData(dropna=False)
    prices=prices.droplevel(1,axis=1)

    real_prices=prices.copy()
    real_prices[[i for i in prices.columns if i!=deflator]]=prices[[i for i in prices.columns if i!=deflator]].div(prices[deflator],axis=0)

    real_rets=(real_prices/real_prices.shift(1)-1).drop([deflator],axis=1).dropna(how='any')
    nominal_rets=(prices/prices.shift(1)-1).drop([deflator],axis=1).dropna(how='any')
    
    real_cov =real_rets.cov()
    real_cov.columns=[ticker_to_name[i] for i in real_cov.columns]  #type:ignore
    real_cov.index=[ticker_to_name[i] for i in real_cov.index]      #type:ignore

    nominal_cov =nominal_rets.cov()
    nominal_cov.columns=[ticker_to_name[i] for i in nominal_cov.columns]    #type:ignore
    nominal_cov.index=[ticker_to_name[i] for i in nominal_cov.index]        #type:ignore

    real_average_returns=real_rets.mean()
    real_average_returns.index=[ticker_to_name[i] for i in real_average_returns.index]  #type:ignore
    real_average_returns.columns=["retorno médio mensal"]

    nominal_average_returns=nominal_rets.mean()
    nominal_average_returns.index=[ticker_to_name[i] for i in nominal_average_returns.index]    #type:ignore
    nominal_average_returns.columns=["retorno médio mensal"]

    js=pd.DataFrame(data=[real_cov.to_json(force_ascii=False), nominal_cov.to_json(force_ascii=False)],columns=["JSON"],index=["real cov","nominal cov"])

    with pd.ExcelWriter(os.path.join("files","History_"+startDate.strftime("%Y%m%d")+"_"+endDate.strftime("%Y%m%d")+".xlsx")) as writer:
        real_rets.to_excel(writer, sheet_name="Retornos_reais")  
        nominal_rets.to_excel(writer, sheet_name="Retornos_nominais")  
        real_cov.to_excel(writer, sheet_name="Covarianca_real")
        nominal_cov.to_excel(writer, sheet_name="Covarianca_nominal")
        real_average_returns.to_excel(writer, sheet_name="Retorno_medio_real")  
        nominal_average_returns.to_excel(writer, sheet_name="Retorno_medio_nominal") 
        js.to_excel(writer, sheet_name="JSON") 
        #cenarios.to_excel(writer, sheet_name="Cenarios")

    for c in real_rets.columns:
        st=shapiro(real_rets[c])

        if st.pvalue<0.05:                #95% de certeza de ser normal
            print("---->",c, "is not shapiro normal. P-value:",st.pvalue)
            st2=shapiro(np.log(1+real_rets[c]))
            if st2.pvalue>0.05:
                print("-- However, it is log normaly distributed with p-value:", st2.pvalue)
        else:
            print("---->",c, "is shapiro normal. P-value:",st.pvalue)


    return real_rets

if __name__ == "__main__":
    if len(sys.argv)<1:
        print("Arguments:")
        print("startDate(yyyy-mm-dd) endDate(yyyy-mm-dd), offshore(true | false")
    else:       
        startDate=datetime.strptime(sys.argv[1],"%Y-%m-%d")
        endDate=datetime.strptime(sys.argv[2],"%Y-%m-%d")
        rets = get_historical_returns(startDate,endDate, sys.argv[3].upper()=="TRUE") 
        print("Data from: ",startDate)
        print("up to: ",endDate)
        print("offshore: ",sys.argv[3].upper()=="TRUE")
        print("monthly historical returns calculated")

        rows=len(rets.columns)
        titles=[]
        for i in rets.columns:
            titles.append(i)
            titles.append(" ")
       
        fig=make_subplots(rows=rows,cols=2,  subplot_titles=titles)
        n=1
        dists=[]
        # plot real rets
        while n<=rows:
            fig.add_trace(go.Histogram(x=rets[rets.columns[n-1]], name=rets.columns[n-1], showlegend=False),row=n,col=1)
            fig=add_qq_fig(rets[rets.columns[n-1]],fig,rets.columns[n-1], n)
            n+=1

        fig.update_layout(title_text="Data from: "+ startDate.strftime("%d-%b-%y")+ " to "+endDate.strftime("%d-%b-%y"))

        fig.write_image(os.path.join("figures" , "history_data.png"))
        fig.show()
            
        sys.exit(0)

     