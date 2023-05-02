from GoogleNews import GoogleNews
from newspaper import Article
import pandas as pd

googlenews=GoogleNews(start='05/01/2020',end='05/31/2020')
googlenews.search('Stock market data')
result=googlenews.result()
df=pd.DataFrame(result)
print(df.head())







