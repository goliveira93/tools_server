#basket_off=[{"Name":"Caixa",     "Ticker":"SPBDUB3T Index", "Source":"Bloomberg"},
#        {"Name":"Renda fixa",    "Ticker":"LBUSTRUU Index", "Source":"Bloomberg"},
#        {"Name":"Hedge funds",   "Ticker":"HFRXGL Index",   "Source":"Bloomberg"},
#        {"Name":"Ações globais", "Ticker":"NDDUWI Index",   "Source":"Bloomberg"}
#        ]


basket_off=[{"Name":"Cash",     "Ticker":"3 month t-bill",  "Source":"Database"},
        {"Name":"Hedge funds",   "Ticker":"HFRX",           "Source":"Database"},
        {"Name":"Renda fixa",    "Ticker":"Bloomberg Agg",  "Source":"Database"},
        {"Name":"Ações globais", "Ticker":"MSCI World",     "Source":"Database"}
        ]



basket_on=[{"Name":"Caixa",           "Ticker":"CDI",               "Source":"Database"},
           {"Name":"Multimercado",    "Ticker":"IFMM",              "Source":"Database"},
           {"Name":"Inflação",        "Ticker":"IMA-B",             "Source":"Database"},
           {"Name":"Ações",           "Ticker":"IBX",               "Source":"Database"}
]

colors=["#2C4257",  
        "#48728A",
        "#708F92",
        "#A3ABA4",
        "#605869",   #cor principal  para texto de corpo
        "#948794",
        "#E7A75F",   #Apenas para detalhes em elementos gráficos
        "#A25B1E"    #Apenas em gráficos
        ]

markers=["circle",
         "cross",
         "square",
         "star",
         "bowtie",
         "triangle-up",
         "y-down",
         "hexagram"

]

describe_layout = dict(
    width=840,
    height=600,
    font={"family":"Segoe UI"},
    legend={"yanchor":"bottom",
            "xanchor":"left",
            "x":0,
            "y":-0.2,
            "orientation":"h"},

    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

boxplot_layout = dict(
    width=722,
    height=972,
    font={"family":"Segoe UI"},
    legend={"yanchor":"middle",
            "xanchor":"right",
            "x":1.2,
            "orientation":"v"},

    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

small_boxplot_layout = dict(
    width=486,
    height=520,
    yaxis={"tickformat":".1%","gridcolor":colors[5],"griddash":'dot',"gridwidth":1, "range":[-0.5,2.5]},
    xaxis={"showticklabels":True},
    font={"family":"Segoe UI"},
    legend={"yanchor":"bottom",
            "xanchor":"left",
            "x":1.1,
            "orientation":"h"},

    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)
