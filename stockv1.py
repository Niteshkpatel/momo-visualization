import pandas as pd
import streamlit as st
import altair as alt
import plotly.graph_objects as go


@st.cache
def load_data():
    df=pd.read_csv('tickers.csv.gz',compression='gzip')
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
    # st.write('Threshold :',threshold)
    return res

data = load_data()


def make_chart():
    c = alt.Chart(momentum_threshold(ticker_data,threshold,option),title='Buy/Sell based upon momentum').mark_line().encode(
    y=alt.Y('Closing Price',impute=alt.ImputeParams(value=None)),
    x = 'Date/Time',
    color='decision',
    ).interactive()

    st.altair_chart(c, use_container_width=True)

    
option = st.selectbox(
     'Select the stock !',
     list(data['Ticker'].unique()))
st.write('You selected:', option)

# ticker=data['Ticker'].unique()[0]
ticker_data = data.loc[data.Ticker==option,['Ticker','Date/Time','Closing Price','MomRank']]

threshold = st.number_input('Momentum Threshold', min_value=0, max_value=400, value=40, help='Set the threshold momentum rank for buy/sell signal')#,on_change=make_chart)
st.write('The current threshold is :', threshold)



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
    # points_made_momo = round(z.loc[z['decision'] == 'sell','Closing Price'].sum() - z.loc[z['decision'] == 'buy','Closing Price'].sum(),2)
    momo_sell = (z.loc[z['decision'] == 'sell',['Date/Time','Closing Price']]).reset_index(drop=True)
    momo_buy = (z.loc[z['decision'] == 'buy',['Date/Time','Closing Price']]).reset_index(drop=True)
    momo_returns = (momo_sell['Closing Price'].div(momo_buy['Closing Price'])-1).sum()+1
    days = ((momo_sell['Date/Time'] - momo_buy['Date/Time']).sum()).days
    CAGR_momo = round((momo_returns **(365/days) - 1)*100,1)
    
    # st.text ("### Absolute points made using Momo model : {}".format(str(points_made_momo)))
    # st.text ("Absolute Momentum returns : {}".format(str(round(momo_returns,2))))
    # st.text ("Annualised momentum returns : {} % for a total holding period of {} days".format((str(CAGR_momo)),days))
    st.markdown ("Absolute Momentum returns : {}".format(str(round(momo_returns,2))))
    st.markdown ("Annualised momentum returns : {} % for a total holding period of {} days".format((str(CAGR_momo)),days))
    Returns(data)
    
    z['Date/Time'] = z['Date/Time'].dt.date
    # z.set_index('Date/Time',inplace=True)
    # z['Closing Price'] = z['Closing Price'].round(2)


    return z

def Returns(data):
    BH_returns = ((data['Closing Price'].tail(1).values / data['Closing Price'].head(1).values)[0])
    days = (data.tail(1)['Date/Time'].values[0] - data.head(1)['Date/Time'].values[0]).astype('timedelta64[D]').astype(int)
    CAGR_BH = round((BH_returns **(365/days) - 1)*100,1)

    # st.text ("Absolute B & H returns : {}".format(str(round(BH_returns,2))))
    # st.text (" Annualised B & H returns : {} % for a total holding period of {} days".format((str(CAGR_BH)),days))
    
    st.markdown("Absolute B & H returns : {}".format(str(round(BH_returns,2))))
    st.markdown ("Annualised B & H returns : {} % for a total holding period of {} days".format((str(CAGR_BH)),days))
    # return (BH_returns,CAGR_BH)

# st.dataframe(Rebalance(momentum_threshold(ticker_data,threshold,option)))


def plotly_table(data):
    fig = go.Figure(data=[go.Table(columnwidth = [400,400,400,400],
    header=dict(values=list(data.columns),
                fill_color='grey',
                line_color='darkslategray',
                font=dict(color='white', size=14),
                height=40,
                align='center'),
    cells=dict(values=[data['Date/Time'], data['Closing Price'],data['decision'],data['MomRank']],
            fill_color='black',
            line_color='darkslategray',
            font=dict(color='white', size=14),
            height=30,
            align='center'))
    ])

    return fig

st.markdown("## Real-Time / Live Momentum Dashboard")

plotly_chart = plotly_table(Rebalance(momentum_threshold(ticker_data,threshold,option)))
make_chart()
st.markdown("## Rebalance history of the stock")
st.plotly_chart(plotly_chart, use_container_width=True)

st.markdown("## Historical distributions of the rank of current stock")
h =alt.Chart(ticker_data).mark_bar().encode(x = alt.X('MomRank',
                                           bin = alt.BinParams(step = 40,extent=[1,400])),
                                 y = 'count()')
st.altair_chart(h, use_container_width=True)

st.button("Re-run")