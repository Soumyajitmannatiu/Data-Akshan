import pandas as pd
import matplotlib.pyplot as plt

# df=pd.read_csv("C:\\Users\\manna\\OneDrive\\Documents\\GitHub\\Data-Akshan\\data\\sales.csv")
# plt.bar(df['Product'],df['Sales'])
# plt.savefig("C:\\Users\\manna\\OneDrive\\Documents\\GitHub\\Data-Akshan\\data\\sales_plot.png")
d1={'Cat':[1,2,3,4,5],'Dog':[1,2,3,4,5]}
df= pd.DataFrame(d1)
df.Cat.astype(int)
print([[column,'datatype='+str(df[column].dtypes)] for column in df.columns])
# print(df['Cat'].dtypes)
print(df.index)