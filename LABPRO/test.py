import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
import random
import firebase_admin
from firebase_admin import credentials,firestore
cred = credentials.Certificate("ServiceKey.json")
firebase_admin.initialize_app(cred)


dataBaseFireBase = firestore.client()


teacherdata=dataBaseFireBase.collection("Users").where(filter=firestore.FieldFilter("Role","==","öğretim görevlisi")).get()
teachersdict={}
for data in teacherdata:
    datas=data.to_dict()
    teachersdict[str(datas["UserID"])]=datas

# print(teachersdict)

busydatadict={}
busydata=dataBaseFireBase.collection("UserBusyTimes").get()
for data in busydata:
    datas=data.to_dict()
    busydatadict[str(datas["userID"])]=datas
# print()

# print(busydatadict)

clasroomsdatadict={}
clasroomdata=dataBaseFireBase.collection("Classrooms").get()

for clsroom in clasroomdata:
    data=clsroom.to_dict()
    clasroomsdatadict[str(data["ID"])]=data

# print(clasroomsdatadict)

def random_room_by_capacity(target_capacity: int | float,room_type: str ,room_map: dict =clasroomsdatadict):

    """
    room_map       : {'D104': {'status': 'NORMAL', 'ID': 'D104', 'capacity': '56'}, ...}
    target_capacity: referans kapasite
    room_type      : "NORMAL" | "LAB"

    Döner          : Şartları sağlayan rastgele oda sözlüğü
    """

    room_type = room_type.upper().strip()          # olası küçük‑büyük harf hatalarını düzelt
    if room_type not in {"NORMAL", "LAB"}:
        raise ValueError('room_type "NORMAL" veya "LAB" olmalı')

    # Kapasite toleranslarını hesapla
    lower, upper = target_capacity * 0.95, target_capacity * 1.15

    # Yardımcı: kapasite farkı gerçekten %5–15 arasında mı?
    def in_range(cap):
        diff_ratio = abs(cap - target_capacity) / target_capacity
        return 0.05 <= diff_ratio <= 0.15

    # Kapasiteyi sayıya çevir, istenen type + kapasite koşulu
    def filter_rooms(desired_type):
        return [
            info | {"capacity": int(info["capacity"])}
            for info in room_map.values()
            if info["status"].upper() == desired_type
               and lower <= int(info["capacity"]) <= upper
               and in_range(int(info["capacity"]))
        ]

    # 1) İstenen type için adaylar
    candidates = filter_rooms(room_type)

    # 2) LAB ise ve aday yoksa → NORMAL’e bak
    if not candidates and room_type == "LAB":
        candidates = filter_rooms("NORMAL")

    # 3) Son hâlâ boşsa → tüm odalardan seç
    if not candidates:
        candidates = [
            info | {"capacity": int(info["capacity"])}
            for info in room_map.values()
        ]

    return random.choice(candidates)


lessondatalist=[]

lessondata=dataBaseFireBase.collection("Lesson").get()

for lesson in lessondata:
    data=lesson.to_dict()
    lessondatalist.append(data)

print(lessondatalist)

def lessons_by_manager( manager_id: str) -> list[dict]:
    """
    lesson_list : [{...}, {...}, ...]  # ders sözlükleri
    manager_id  : aranan lessonManager UUID'si

    Döner       : manager_id ile eşleşen derslerin listesi
    """
    return [lesson for lesson in lessondatalist if lesson.get("lessonManager") == manager_id]


def lessonsEqSync( syncCode: str) -> list[dict]:
    """
    lesson_list : [{...}, {...}, ...]  # ders sözlükleri
    manager_id  : aranan lessonManager UUID'si

    Döner       : manager_id ile eşleşen derslerin listesi
    """
    return [lesson for lesson in lessondatalist if lesson.get("lessonManager") == syncCode]





def create_weekly_schedule():
    weekdays = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
    time_slots = [
        "09:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00",
        "13:00-14:00", "14:00-15:00", "15:00-16:00", "16:00-17:00",
        "17:00-18:00", "19:00-21:00"
    ]

    # DataFrame oluştur
    df = pd.DataFrame(columns=["Gün", "Saat", "1. Sınıf", "2. Sınıf", "3. Sınıf", "4. Sınıf"])
    for day in weekdays:
        for time in time_slots:
            df.loc[len(df)] = [day, time, np.nan, np.nan, np.nan, np.nan]

    # MultiIndex ayarla
    df.set_index(["Gün", "Saat"], inplace=True)

   

    return df
    





dfBLM=create_weekly_schedule()
dfYZM=create_weekly_schedule()

def selector(id):
        
        return busydatadict[id]

class UserAvaible():
    def __init__(self,UserId):
        self.id=UserId

        self.df=create_weekly_schedule()
        busydata=selector(str(self.id))
        self.timeslist=list(set(busydata["times"]))
            
            
            
        for frame in self.timeslist:
            framelist=frame.split(",")
            timerange=framelist[1]+"-"+framelist[2]

            for column in self.df.columns:
                    
                self.df.at[(framelist[0],timerange),column]="xxx"
        
    def isavaible(self,day,timearrange):

        return self.df.at[(day,timearrange),"1. Sınıf"]!="xxx"

    





def createprogram():
    # Programı çalıştır
    



    


    userbusytimes=[]
    rektorluk=UserAvaible("Özel")
    nowUser=None

    for teacher in  busydatadict.keys():
        if UserAvaible(teacher).id=="Özel":
            continue

        userbusytimes.append(UserAvaible(teacher))


    for teacher in userbusytimes:

        teacherid=teacher.id

        teacherlessons=lessons_by_manager(teacherid)


























        
    

    

        

createprogram()