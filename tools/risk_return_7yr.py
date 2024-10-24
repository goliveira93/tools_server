from et_lib.ET_Data_Reader import BasketHistoricalData;
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.validators.scatter.marker import SymbolValidator
import pandas as pd
from settings import colors, markers
from datetime import datetime
import os


chart_layout = dict(
    width=1500,
    height=2000,
    margin={"l":100,"r":20},
    font={"family":"Segoe UI"},
    legend={"yanchor":"middle",
            "xanchor":"center",
            "x":0.5,
            "y":0.47,
            "orientation":"h"},
    #shapes=recs,
    xaxis={
        "tickformat":".0%",
        "title":"risco (volatilidade)"
        },
    yaxis={
        "tickformat":".0%",
        "title":"retorno mensal anualizado"
        },
    yaxis2={
        "tickformat":".0%",
        "title":"retorno mensal anualizado"
        },
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

def make_scatter(basket,names, startDate, endDate, years=7, inflation_index=None):

    names = names +["Inflação (nominal)"]
    bb= BasketHistoricalData("basket", startDate,endDate, basket)
    bb.loadFromBloomberg(periodicity="MONTHLY")
    bb.loadFromDatabase(periodicity="MONTHLY")
    prices=bb.getData().droplevel(1,axis=1)
    
    if inflation_index is None:
        prices[inflation_index]=[1 for _ in prices.index]

    prices_back=prices[inflation_index]                   #type: ignore
    prices=prices.div(prices[inflation_index], axis=0)    #type: ignore
    prices[inflation_index]=prices_back
    prices=prices.drop(columns=[inflation_index])

    #prices=prices.drop(columns=[inflation_index])
    rets=(prices/prices.shift(1)-1).dropna(how="any")
    
    i=years*12
    if i>=len(rets):
        print("Historico não é longo o bastante.")
        return None

    idx=[]
    d=pd.DataFrame()
    while i<len(rets):
        idx.append(rets.index[i])
        m=rets[i-years*12:i].mean(axis="index")
        s=rets[i-years*12:i].std(axis="index")
        dd=pd.concat([m,s],axis=1)
        dd.columns=["mean","std"]  #type:ignore
        d=pd.concat([d,dd],axis=0)
        i+=1

    print(d)
    d["mean"]=d["mean"]*12
    d["std"]=d["std"]*(12**0.5)

    mean=[]
    for i in prices.columns:
        q1=d.loc[i].quantile(0.25)
        q3=d.loc[i].quantile(0.75)
        q2=d.loc[i].median()
        mi=[min(q2[c]-d.loc[i][c].min(),1.5*(q3[c]-q1[c])+(q2[c]-q1[c])) for c in ["mean","std"]]
        mib=[q3[c] for c in ["mean","std"]]
        ma=[min(d.loc[i][c].max()-q2[c],1.5*(q3[c]-q1[c])+(q3[c]-q2[c])) for c in ["mean","std"]]
        mab=[(q1[c]) for c in ["mean","std"]]
        mean.append([i, q2[0], q2[1] ,ma[0], ma[1], mi[0], mi[1],mab[0],mab[1],mib[0],mib[1]])
    md=pd.DataFrame(data=mean,columns=["benchmark","median_y", "median_x", "max_y", "max_x", "min_y", "min_x", "q1_y", "q1_x", "q3_y", "q3_x"])
    md=md.set_index("benchmark")

    fig=make_subplots(rows=2,cols=1)
    for n,i in enumerate(prices.columns):
        fig.add_trace(go.Scatter(x=d.loc[i]["std"], y=d.loc[i]["mean"], mode="markers", marker={"color":colors[n],"size":5}, marker_symbol=markers[n], name=names[n], legendgroup="Scatter"),row=1,col=1)

    recs=[]
    for n,i in enumerate(prices.columns):
            recs.append({"type" : "rect", "fillcolor" : colors[n],"opacity":0.3,
                "fillcolor" : colors[n],
                "opacity":0.3,
                "x0":md.loc[i]["q1_x"],
                "x1":md.loc[i]["q3_x"],
                "y0":md.loc[i]["q1_y"],
                "y1":md.loc[i]["q3_y"],
                "line":{"width":0}})
            fig = fig.add_trace(go.Scatter(x=[md.loc[i]["median_x"]], y=[md.loc[i]["median_y"]], mode="markers", marker={"color":colors[n], "size":1, "opacity":0.3},
                                        error_x={"type":"constant", "symmetric":False, "value":md.loc[i]["max_x"], "valueminus":md.loc[i]["min_x"], "visible":True},
                                        error_y={"type":"constant", "symmetric":False, "value":md.loc[i]["max_y"], "valueminus":md.loc[i]["min_y"], "visible":True},
                                        showlegend=True,
                                        name=names[n],legendgroup="box"),row=1,col=1)

    fig.update_layout(chart_layout)
    fig.update_layout(shapes=recs)
    if inflation_index is None:
        title="Retornos nominais médios em janelas de "+str(years)+" anos. Desde "+(rets.index[0]).strftime("%d-%b-%y")+ " até "+ (rets.index[-1]).strftime("%d-%b-%y") #type: ignore
    else:
        title="Retornos reais médios em janelas de "+str(years)+" anos. Desde "+(rets.index[0]).strftime("%d-%b-%y")+ " até "+ (rets.index[-1]).strftime("%d-%b-%y")     #type: ignore
    fig.update_layout(title=title)  #type: ignore

    for n,i in enumerate(prices.columns):
        fig.add_trace(go.Scatter(x=idx, y=d.loc[i]["mean"], mode="lines", line={"color":colors[n], "dash":"dot"}, name=names[n], legendgroup=names[n]),row=2,col=1)
        fig.add_trace(go.Scatter(x=idx, y=[d.loc[i]["mean"].mean() for _ in d.loc[i]["mean"].index], mode="lines", marker={"color":colors[n]}, name=names[n], legendgroup=names[n], showlegend=False),row=2,col=1)
    return fig
    

basket = [{"Ticker" :"SPBDUB3T Index", "Source":"Bloomberg", "Proxy ticker":"fed_funds", "Proxy source":"Database" },
          {"Ticker" :"HFRXGL Index",   "Source":"Bloomberg"},
          #{"Ticker" :"XAU Curncy",   "Source":"Bloomberg"},
          {"Ticker" :"LBUSTRUU Index", "Source":"Bloomberg"},
          {"Ticker" :"NDDUWI Index",   "Source":"Bloomberg"},
          {"Ticker" :"CPURNSA Index",  "Source":"Bloomberg"}]
names = ["Caixa", "Hedge funds", "Renda fixa" ,  "Ações globais"] 
inflation_index="CPURNSA Index"

simulations=[
    {"name": "inflação alta",  "start_date": datetime.strptime("1976-03-31","%Y-%m-%d"), "end_date" : datetime.strptime("1982-09-30","%Y-%m-%d"), "anos":5},  #idealmente 06-30-1962
    {"name": "inflação media", "start_date": datetime.strptime("1982-09-30","%Y-%m-%d"), "end_date" : datetime.strptime("2008-07-31","%Y-%m-%d"), "anos":7},
    {"name": "inflação baixa", "start_date": datetime.strptime("2008-07-31","%Y-%m-%d"), "end_date" : datetime.strptime("2020-04-30","%Y-%m-%d"), "anos":7}
]

#basket = [{"Ticker" :"BZACCETP Index", "Source":"Bloomberg"},
#          {"Ticker" :"IFMMIFMM Index", "Source":"Bloomberg"},
#          {"Ticker" :"BZRFIMAB Index", "Source":"Bloomberg"},
#          {"Ticker" :"IBX Index",      "Source":"Bloomberg"},
#          {"Ticker" :"BZPIIPCA Index", "Source":"Bloomberg"}]
#names = ["Caixa", "Multimercado", "Inflação" ,  "Ações"] 
#inflation_index="BZPIIPCA Index"

#simulations=[
#    {"name": "brasil", "start_date": datetime.strptime("2003-09-30","%Y-%m-%d"), "end_date" : datetime.strptime("2022-10-31","%Y-%m-%d")}
#    ]
#      

for s in simulations:

    startDate=s["start_date"]
    endDate=  s["end_date"]
    assert isinstance(startDate,datetime)
    assert isinstance(endDate,datetime)

    #fig=make_scatter(benchmarks,names, startDate,endDate,years=7)
    #fig.show()

    fig=make_scatter(basket,names, startDate,endDate,years=s["anos"], inflation_index=inflation_index)
    if fig is not None:
        fig.update_layout(
            xaxis={"griddash":'dot', "gridcolor":colors[7]},
            yaxis={"griddash":'dot', "gridcolor":colors[7]},
            title={"font" : {"family":"Segoe UI"},
                "text" : s["name"]+": "+startDate.strftime("%b-%Y")+" - "+endDate.strftime("%b-%Y"+"\n"+"retonros de "+str(s["anos"])+" anos")
                }
        )
        fig.write_image(os.path.join("figures",s["name"]+"_"+startDate.strftime("%Y%m%d")+"_"+endDate.strftime("%Y%m%d")+".png"))



