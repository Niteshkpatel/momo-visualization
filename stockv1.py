import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import os


@st.cache
def load_data():
    script_dir = os.path.dirname(__file__)
    rel_path = "/tickers.csv.gz"
    abs_file_path = os.path.join(script_dir, rel_path)
    df=pd.read_csv(abs_file_path,compression='gzip')
    df=df.drop(df.columns[0],axis=1)
    df['Date/Time'] =  pd.to_datetime(df['Date/Time'], infer_datetime_format=True)

    # momentum_threshold = 400
    # def categorise(row):  
    #     if row['MomRank'] > momentum_threshold:
    #         return 'sell'
    #     return 'buy'
    # df['decision'] = df.apply(lambda row: categorise(row), axis=1)
    data =df.loc[:,['Ticker','Date/Time','Closing Price','MomRank']]
    return data

def momentum_threshold(data,threshold,ticker):#########
    
    # ticker=data['Ticker'].unique()[0]
    # res = data.loc[data.Ticker==ticker,['Ticker','Date/Time','Closing Price','MomRank']]

    def categorise(row):  
        if row['MomRank'] > threshold:
            return 'sell'
        return 'buy'
    res = data.copy(deep=True)
    res['decision'] = res.apply(lambda row: categorise(row), axis=1)
    res =res.loc[data.Ticker==ticker,['Date/Time','Closing Price','decision','MomRank']]#######
    st.write('Threshold :',threshold)
    return res

data = load_data()


def make_chart():
    c = alt.Chart(momentum_threshold(ticker_data,threshold,option),title='Buy/Sell based upon momentum').mark_line().encode(
    y=alt.Y('Closing Price',impute=alt.ImputeParams(value=None)),
    x = 'Date/Time',
    color='decision',
    ).interactive()

    st.altair_chart(c, use_container_width=True)

    h =alt.Chart(ticker_data).mark_bar().encode(x = alt.X('MomRank',
                                           bin = alt.BinParams(step = 40,extent=[1,400])),
                                 y = 'count()')
    st.altair_chart(h, use_container_width=True)
option = st.selectbox(
     'Select the stock !',
     list(data['Ticker'].unique()))
st.write('You selected:', option)

# ticker=data['Ticker'].unique()[0]
ticker_data = data.loc[data.Ticker==option,['Ticker','Date/Time','Closing Price','MomRank']]

threshold = st.number_input('Momentum Threshold', min_value=0, max_value=400, value=40, help='Set the threshold momentum rank for buy/sell signal')#,on_change=make_chart)
st.write('The current number is :', threshold)
st.title("Real-Time / Live Momentum Dashboard")
make_chart()


def Rebalance(data):
    data['mask'] = data.loc[:,'decision'] != data['decision'].shift()
    x= data.loc[data['mask'] == True, ['Date/Time','Closing Price','decision','MomRank']]
    z = x
    z.reset_index(inplace=True)
    z=z.drop('index',axis=1)
    if z.loc[:,'decision'].values[1] == 'buy':
      z.drop(0,inplace=True)
    if z.loc[:,'decision'].values[-1] == 'buy': #change it to buy
        v = data.tail(1)
        v=v.replace('buy','sell')
        v=v.drop('mask',axis=1)
        z = pd.concat([z,v])
    z.reset_index(inplace=True)
    z=z.drop('index',axis=1)
    points_made_momo = (z.loc[z['decision'] == 'sell','Closing Price'].sum() - z.loc[z['decision'] == 'buy','Closing Price'].sum())
    st.text ("### Absolute points made using Momo model : {}".format(str(points_made_momo)))
    Returns(data)
    return z

def Returns(data):
    BH_returns = round((data['Closing Price'].tail(1).values / data['Closing Price'].head(1).values)[0],2)
    days = (data.tail(1)['Date/Time'].values[0] - data.head(1)['Date/Time'].values[0]).astype('timedelta64[D]').astype(int)
    CAGR_BH = BH_returns **(252/days) - 1

    st.text ("### Absolute B & H returns : {}".format(str(BH_returns)))
    st.text ("### Annualised B & H returns : {}".format(str(CAGR_BH)))

    # return (BH_returns,CAGR_BH)

st.markdown("### Detailed Data View")
st.dataframe(Rebalance(momentum_threshold(ticker_data,threshold,option)))

st.button("Re-run")