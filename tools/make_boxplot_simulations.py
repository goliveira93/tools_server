from et_lib.ET_macro import get_perfis
from ctypes import CDLL, POINTER
from ctypes import c_size_t, c_double
import os
import h5py
import numpy as np
import plotly.graph_objects as go
from settings import colors, boxplot_layout

nome_perfil="offshore 2023"

def c_drawdown(prices):
    answer = c_lib.drawdown(prices, prices.size)
    return answer

def calc_range(values)->list:
    q1 = np.percentile(values, 25)
    q3= np.percentile(values,75)
    iqd = abs(q3-q1)
    return [q1-1.5*iqd, q3+1.5*iqd]


libname = os.path.join("..","etrnty_investimentos","etrnty_investimentos","atuario","wealth.dll")
c_lib = CDLL(libname)
ND_POINTER_1 = np.ctypeslib.ndpointer(c_double, flags="C")
c_lib.drawdown.argtypes = [ND_POINTER_1, c_size_t]
c_lib.drawdown.restype = c_double


sim_file=os.path.join("..","etrnty_investimentos","etrnty_investimentos","atuario","forecasts",nome_perfil+".hdf5")
perfis=get_perfis(nome_perfil)

f = h5py.File(sim_file, 'r')

z = list(f.get('index'))  #type: ignore
idx=[i.decode('UTF-8') for i in z]

for dataset,title in zip(["data","data_nominal"],["(valores reais)", "(valores nominais)"]):
    rets= np.array(f.get(dataset))[:,:,:120]
    fig_return=[go.Figure(),go.Figure()]
    fig_drawdown=[go.Figure(),go.Figure()]
    ret_ranges=[]
    dd_ranges=[]
    for e,p in enumerate([i for i in perfis if i["nome_perfil"]!="customizado"]):
        w = [p["pesos"][i] for i in idx]
        sim_rets   = np.array([np.dot(w,rets[i]) for i in range(rets.shape[0])])

        sim_prices = np.cumprod((sim_rets+1),axis=1)
        a          = np.ones(sim_prices.shape[0])
        sim_prices = np.insert(sim_prices,0,a,axis=1)

        drawdowns  = np.array([c_drawdown(i) for i in sim_prices])
        final_prices=sim_prices[:,-1]
        final_prices=final_prices-1

        fig_return[0].add_trace(go.Box(y=final_prices,name=p["nome_perfil"],boxpoints='all',marker_color=colors[e],jitter=0.3, marker_size=1))
        fig_drawdown[0].add_trace(go.Box(y=drawdowns,name=p["nome_perfil"],boxpoints='all',marker_color=colors[e],jitter=0.3, marker_size=1))
        fig_return[1].add_trace(go.Box(y=final_prices,name=p["nome_perfil"],boxpoints='all',line_color=colors[e],marker_color='white',jitter=0, marker_size=1))
        fig_drawdown[1].add_trace(go.Box(y=drawdowns,name=p["nome_perfil"],boxpoints='all',line_color=colors[e],marker_color='white',jitter=0, marker_size=1))
        ret_ranges.append(calc_range(final_prices))
        dd_ranges.append(calc_range(drawdowns))

    ret_range=[min([i[0] for i in ret_ranges]), max([i[1] for i in ret_ranges])]
    dd_range=[min([i[0] for i in dd_ranges]), max([i[1] for i in dd_ranges])]

    fig_return[0].update_layout(boxplot_layout, title="Retorno acumulado "+title, yaxis={"tickformat":".1%"}, showlegend=False,height=722)
    fig_drawdown[0].update_layout(boxplot_layout, title="Maior drawdown "+title, yaxis={"tickformat":".1%"}, showlegend=False,height=722)
    fig_return[1].update_layout(boxplot_layout, title="Retorno acumulado "+title, yaxis={"tickformat":".1%", "range":ret_range}, showlegend=False,height=722)
    fig_drawdown[1].update_layout(boxplot_layout, title="Maior drawdown "+title, yaxis={"tickformat":".1%", "range":dd_range}, showlegend=False,height=722)

    fig_return[0].write_image(os.path.join("figures","box_points_retorno_"+title+".png"))
    fig_drawdown[0].write_image(os.path.join("figures","box_points_dd_"+title+".png"))
    fig_return[1].write_image(os.path.join("figures","box_retorno_"+title+".png"))
    fig_drawdown[1].write_image(os.path.join("figures","box_dd_"+title+".png"))

    
    fig_return[0].show()
    fig_drawdown[0].show()
    fig_return[1].show()
    fig_drawdown[1].show()

f.close()

