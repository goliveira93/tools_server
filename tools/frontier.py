import pymysql
import pandas as pd
import json
#import h5py
import plotly.graph_objects as go
import numpy as np
import numpy.typing as npt
from math import sqrt
from settings import basket_on
import scipy.optimize as optimization
from settings import describe_layout, colors, boxplot_layout, small_boxplot_layout


def get_db(autocommit:bool = True)->pymysql.Connection:
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
                database="cenarios_macro",
                autocommit=autocommit,
                cursorclass=pymysql.cursors.DictCursor)         # type: ignore
        return mydb
    except:
        raise



def statistics(weights, returns, cov):
    portfolio_return = np.exp(np.dot(weights,returns)*12)-1
    portfolio_volatility = np.sqrt(np.dot(weights, np.dot(weights,cov))*12)
    return np.array([portfolio_return[0], portfolio_volatility,
                     portfolio_return[0] / portfolio_volatility])

# scipy optimize module can find the minimum of a given function
# the maximum of a f(x) is the minimum of -f(x)
def min_function_sharpe(weights, returns, cov):
    return -statistics(weights, returns,cov)[2]

def max_returns(weights, returns, cov):
    return -statistics(weights, returns,cov)[0]


def optimize_portfolio(weights, returns,target_vol):
    def vol(weights):
        portfolio_volatility = np.sqrt(np.dot(weights, np.dot(weights,cov))*12)
        return portfolio_volatility

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                   {'type': 'ineq', 'fun': lambda x: target_vol-vol(x)})
    bounds = tuple((0, 1) for _ in range(len(weights)))
    return optimization.minimize(fun=max_returns, x0=weights, args=(returns,cov)
                                 , method='SLSQP', bounds=bounds, constraints=constraints)
    

def plot_expected_frontier(expected_returns, cov):
        basket=basket_on
        tmp=np.sqrt(cov*12)

        y=np.exp(expected_returns*12)-1
        x=[tmp[j,j] for j in range(0,len(tmp))]

        texts=[i["Name"] for i in basket]

        fig=go.Figure()
        #fig.add_trace(go.Scatter(x=x, y=y,text=texts, textposition="top right", mode="markers, text", name="Risco x retorno"))
        fig.update_layout(
                width=840*0.9,
                height=600*0.9,
                font={"family":"Segoe UI"},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis={
                "tickformat":".1%",
                "title":{"text": "retorno real anualizado (%)"},
                "showline":True,
                "griddash":None
                },
                xaxis={
                "tickformat":".1%",
                "title":{"text": "volatilidade anualizada (%)"},
                "showline":True
                },
                legend={"yanchor":"bottom",
                    "y":0,
                    "xanchor":"right",
                    "x":1,
                    "orientation":"v",
                    "font":{"size":10}},
        )
        return fig
        
        
def get_sims(nome_projecao:str, nome_cenario: str)-> list:
    db=get_db()
    sql="SELECT matriz_covarianca FROM projecoes WHERE nome_projecao='"+nome_projecao+"';"
    crsr=db.cursor()
    crsr.execute(sql)
    rows = crsr.fetchone()
    cov_matrix=pd.read_json(rows["matriz_covarianca"])
    sql= "SELECT retornos_esperados FROM retornos_esperados WHERE nome_projecao='"+nome_projecao+"' AND nome_cenario='"+nome_cenario+"';"
    crsr.execute(sql)
    rows = crsr.fetchone()
    x=json.loads(rows["retornos_esperados"])
    returns=pd.DataFrame(data=[float(y) for y in x.values()], index=x.keys())
    returns=returns.reindex(index=cov_matrix.index)
    return [cov_matrix.to_numpy(), returns.to_numpy(),cov_matrix.index]

if __name__ == "__main__":
        [cov,rets,names] = get_sims("offshore 2023","inflação alta")
        fig=plot_expected_frontier(rets,cov)
        fig.show()
        x=[]
        y=[]
        w=[]
        for vol in [0.03,0.05,0.07,0.09,0.11]:
            optimum=optimize_portfolio([1/len(rets) for _ in range (len(rets))], rets,vol)
            stats=statistics(optimum['x'],rets,cov)
            x.append(stats[1])
            y.append(stats[0])
            w.append(optimum['x'])
            #txt="CDI: "+str((optimum['x'][0]*100).round(1))+"%<br>"
            #txt+="Multimercado: "+str((optimum['x'][1]*100).round(1))+"%<br>"
            #txt+="Inflação:"+str((optimum['x'][2]*100).round(1))+"%<br>"
            #txt+="Bolsa:"+str((optimum['x'][3]*100).round(1))+"%<br>"
            #fig.add_trace(go.Scatter(x=[x[-1]], y=[y[-1]], textposition=pos, mode="markers+text", name=port_name,text=txt, marker_color=colors[0],showlegend=False,textfont={"size":10}))        
        df=pd.DataFrame(w,columns=names)
        print(df)
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name="Sem restrições", marker_color=colors[0],showlegend=False,textfont={"size":10}))        

        #CDI=statistics([1,0,0,0],rets.T,cov)
        #MM=statistics([0,1,0,0],rets.T,cov)
        #NTNB=statistics([0,0,1,0],rets.T,cov)
        #IBX=statistics([0,0,0,1],rets.T,cov)
        #fig.add_trace(go.Scatter(x=x, y=y, textposition="middle right", mode="lines+markers", name="Sem restrições", marker_color=colors[0],showlegend=True))        
        #for i,n,m in zip([CDI,MM,NTNB,IBX],["CDI","Multimercado","Inflação","Bolsa"],["star","cross","bowtie","diamond"]):
        #    fig.add_trace(go.Scatter(x=[i[1]], y=[i[0]], textposition="middle right", mode="markers", name=n, marker_color=colors[6],marker_symbol=m,marker_size=8,showlegend=True))        

        #weights=[
        #    [0.60,0.25,0.15,0.00],
        #    [0.40,0.25,0.30,0.05],
        #    [0.20,0.30,0.40,0.10],
        #    [0.10,0.25,0.45,0.20],
        #    [0.05,0.15,0.50,0.30]
        #]
        #x=[statistics(w,rets.T,cov)[1] for w in weights]
        #y=[statistics(w,rets.T,cov)[0] for w in weights]
        #fig.add_trace(go.Scatter(x=x, y=y, textposition="middle right", mode="lines+markers", name="Perfis recomendados", marker_color=colors[2],showlegend=True))        

        fig.write_html('HTML/frontier.html', auto_open=True)
        fig.write_image("figures/frontier_portfolios.png")
        

