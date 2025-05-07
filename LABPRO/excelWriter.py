import website.DataBaseManager as DataBaseManager

import pandas as pd
import numpy as np

database=DataBaseManager.FirebaseManager()
df1=pd.read_excel("universiteVerisi.xlsx",sheet_name="User Giriş")
useridlist=df1["User ID"].tolist()
for index in range(len(df1.index)):
    data=df1.iloc[index]
    database.add_user(int(data["User ID"]),data["Name"],data["Email"],data["Rol"])

df2=pd.read_excel("universiteVerisi.xlsx",sheet_name="Derslik Giriş")

for index in range(len(df2.index)):
    data=df2.iloc[index]
    database.add_classroom(data["Derslik ID"],int(data["Kapasite"]),data["Statü"])
    




df3=pd.read_excel("universiteVerisi.xlsx",sheet_name="Ders Tanım")

for index in range(len(df3.index)):
    data=df3.iloc[index]
    


df4=pd.read_excel("universiteVerisi.xlsx",sheet_name="User Meşgül Saatleri")

for index in range(len(df4.index)):
    data=df4.iloc[index]
    try:
        UserId=int(data["User"])
    except:
        UserId=data["User"]
    time=data["Zaman"].split(",")
    if UserId in useridlist:
        
        database.add_user_busytime(UserId,time[0],time[1],time[2])
    else:

        database.add_user_busytime("Özel",time[0],time[1],time[2])

