import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
import pandas as pd
import numpy as np

register_matplotlib_converters()

def killer():
    plt.close("all")

def gen_plt(symbol, currency):
    plt.style.use('dark_background')
    fig1, ax = plt.subplots(figsize = (8,5))
    ax.set_title(symbol)
    ax.set_ylabel(currency)
    #ax.spines["top"].set_visible(False)
    #ax.spines["right"].set_visible(False)
    #ax.spines["bottom"].set_visible(False)
    #ax.spines["left"].set_visible(False)
    #ax.get_xaxis().tick_bottom()
    #ax.get_yaxis().tick_left()
    #ax.set_axisbelow(True)
    #ax.yaxis.grid(color='gray', linewidth=0.25)
    ax.xaxis.grid(color='white', linewidth=0.25, alpha=0.9)
    return fig1, ax

def pe_calc(df_daily, e_total_index, e_total, grw_exp):
    df_daily["blended_earnings"] = np.interp(df_daily.index.values.astype('datetime64[D]').astype(int) , e_total_index, e_total)
    df_daily["blended_pe"] = df_daily["Close"]/df_daily["blended_earnings"]

    #normal_multiple_deprecated = df_daily["blended_pe"].mean()
    normal_multiple = df_daily["blended_pe"].agg(lambda x: x[x>0].median())
    current_pe = df_daily["blended_pe"].iloc[-1]
    e_multiple = grw_exp

    if style == "PE15":
        e_multiple = 15.0
    elif style == "Base":
        if e_multiple < 15.0:
            e_multiple = 15.0
    elif style == "PEG85":
        if e_multiple <0:
            e_multiple = 8.5
        else:
            e_multiple = e_multiple + 8.5

    return e_multiple, normal_multiple, current_pe

def grw_calc(e_total):
    for i, item in enumerate(e_total):
        if item>0:
            grw_start = i
            grw_status = True
            break
    if e_total[-1]<0:
        grw_status = False

    if grw_status:
        num_years = len(e_total)-grw_start-1
        if num_years == 1:
            print("Short Earnings Growth History.")
            grw_exp = (((e_total[-1]/e_total[-2])**(1/1))-1)*100 #TODO: improve grw_exp
        else:
            grw_exp = (((e_total[-1]/e_total[-3])**(1/2))-1)*100 #TODO: improve grw_exp
        grw = (((e_total[-1]/e_total[i])**(1/num_years))-1)*100 #(start/end)^(1/periods)-1
    else:
        grw = 0
        grw_exp = 0
    return grw, grw_exp

def data_processing(df_daily ,df_yearly, df_est, symbol, style, currency):
    killer()
    earnings_col = df_yearly.filter(like='Earn').columns[0]
    ocf_col = df_yearly.filter(like='Operati').columns[0]
    dividend_col = df_yearly.filter(like='Divid').columns[0]
    shares_col = df_yearly.filter(like='Divid').columns[0]

    price = np.array(df_yearly.index.values)
    for x in df_est.index.values:
        if not pd.isnull(x):
            price = np.append(price, x)

    e_total = np.append(pd.to_numeric(df_yearly[earnings_col].values, errors='coerce'),pd.to_numeric(df_est["Median EPS"].values, errors='coerce'))#TODO:remove duplicate
    thecutter = ~np.isnan(e_total)
    e_total = e_total[thecutter]

    cut = (len(price)-len(e_total))


    e_total_index = np.append(df_yearly.index.values.astype('datetime64[D]').astype(int),df_est.index.values.astype('datetime64[D]').astype(int))
    e_total_index = e_total_index[thecutter]

    print(price)
    print(e_total_index)

    grw, grw_exp = grw_calc(e_total)

    e_multiple, normal_multiple, current_pe = pe_calc(df_daily, e_total_index, e_total, grw_exp, style)

    e_total_norm= e_total * normal_multiple
    e_total = e_total * normal_multiple
    df_yearly[earnings_col] = df_yearly[earnings_col].apply(lambda x: x*e_multiple)
    df_est["Median EPS"] = df_est["Median EPS"]*e_multiple

    #e_total = np.append(pd.to_numeric(df_yearly[earnings_col].values, errors='coerce'),pd.to_numeric(df_est["Median EPS"].values, errors='coerce'))

    e_total = e_total[~np.isnan(e_total)]
    price = price[(len(price)-len(e_total)):]
    print(price)
    xlabel = []
    for x in df_yearly.index:
        if not pd.isnull(x):
            xlabel.append(x.strftime('%m/%y'))
    for x in df_est.index:
        if not pd.isnull(x):
            xlabel.append(x.strftime('%m/%y'))

    fig1, ax = gen_plt(symbol, currency)

    if style == "REIT":
        ax.set_ylabel("OCF")
        df_yearly[dividend_col] = df_yearly[dividend_col].apply(lambda x: x*15)
        df_yearly[ocf_col] = df_yearly[ocf_col]/df_yearly[shares_col]
        df_yearly[ocf_col] = df_yearly[ocf_col].apply(lambda x: x*15)
        plt.fill_between(df_yearly.index, df_yearly[ocf_col], color = "blue")
        plt.plot(df_daily.index, df_daily["Close"], color="white")
        plt.plot(df_yearly.index, df_yearly[ocf_col], color="grey", linewidth=3, marker="^")
        plt.plot(df_yearly.index, df_yearly[dividend_col], color="yellow", marker="o")
        cutvar = xlabel[cut:]
        plt.xticks(price[:-1],cutvar[:-1])
        plt.ylim(0,None)
        plt.xlim(df_yearly.index[cut],price[-2])
        ax.xaxis.grid(color='white', linewidth=0.25, alpha=0.95)
        df_yearly[dividend_col] = df_yearly[dividend_col].apply(lambda x: x*(1/15))
        df_yearly[ocf_col] = df_yearly[ocf_col].apply(lambda x: x*(1/15))

    elif style == "PE-Plot":
        plt.plot(df_daily["blended_pe"],color="orange")
        if df_daily["blended_pe"].max() > 100.0 and df_daily["blended_pe"].min() < 0.0:
            plt.ylim(0,100)
        elif df_daily["blended_pe"].min() < 0.0:
            plt.ylim(0,None)
        elif df_daily["blended_pe"].max() > 100.0:
            plt.ylim(0,100)
        ax.set_ylabel("PE")
        cutvar = xlabel[cut:]
        plt.xticks(price[:-1],cutvar[:-1])
        plt.xlim(df_yearly.index[cut],price[-2])
    else:
        df_yearly[dividend_col] = df_yearly[dividend_col].apply(lambda x: x*e_multiple)
        plt.fill_between(price, e_total, color = "blue")
        plt.xticks(price,xlabel[cut:])
        plt.plot(price, e_total_norm, color="orange", marker="o")
        plt.plot(price, e_total, color="grey", linewidth=3, marker="^")
        plt.plot(df_yearly.index, df_yearly[dividend_col], color="yellow", marker="o")
        plt.plot(df_daily.index, df_daily["Close"], color="white")
        plt.ylim(0,None)
        plt.xlim(df_yearly.index[cut],price[-1]) #df_est.index[len(df_est.index)-1])
        ax.xaxis.grid(color='white', linewidth=0.25, alpha=0.95)
        df_yearly[earnings_col] = df_yearly[earnings_col].apply(lambda x: x*(1/e_multiple))
        df_yearly[dividend_col] = df_yearly[dividend_col].apply(lambda x: x*(1/e_multiple))
        df_est["Median EPS"] = df_est["Median EPS"]*(1/e_multiple)

    plt.savefig('plot.png')
    #Cleanup
    plt.clf()
    plt.cla()
    return(current_pe, normal_multiple, grw, grw_exp)
