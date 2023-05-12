from GoogleNews import GoogleNews
# from newspaper import Article
import pandas as pd

googlenews=GoogleNews(start='05/01/2020',end='05/31/2020')
googlenews.search('Stock market indian news')
result=googlenews.result()
df=pd.DataFrame(result)
print(result)
# result = result.
# for i in range(df["title"].siz
# e-1):
#           print(df.loc[i,"title"])







