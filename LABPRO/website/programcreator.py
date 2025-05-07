"""
Otomatik Ders Programı – Döneme Göre Filtreli Yerleştirme (05 May 2025)
-----------------------------------------------------------------------
‘bahar’ için pastyear ∈ {2,4,6,8}, ‘güz’ için pastyear ∈ {1,3,5,7} dersleri kullanır.
Diğer kurallar ve esneklikler önceki sürümle aynıdır.
"""

import datetime
import pandas as pd
import numpy as np
import random
from collections import defaultdict
import re
import firebase_admin
from firebase_admin import credentials, firestore

# ------------------------------ Firebase init (modül seviyesinde sadece initialize)
cred = credentials.Certificate("ServiceKeyvuzok.json")
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)

# Firestore istemcisi ve global placeholderlar
db = None
teachersdict = None
busydatadict = None
classroomdatadict = None
lessondatalist = None

def getData():
    """
    Firestore’dan yalnızca ihtiyaç anında tüm verileri çeker
    ve helper map’leri günceller.
    """
    global db, teachersdict, busydatadict, classroomdatadict, lessondatalist, teacher_names

    # Firestore istemcisi
    db = firestore.client()

    # 1) Öğretim görevlileri
    teachersdict = {
        d["UserID"]: d
        for doc in db.collection("Users")
                     .where(filter=firestore.FieldFilter("Role", "==", "öğretim görevlisi"))
                     .get()
        for d in [doc.to_dict()]
    }
    # **teacher_names** haritasını da burada oluşturuyoruz
    teacher_names = {
        uid: info["name"]
        for uid, info in teachersdict.items()
    }

    # 2) Meşgul zaman blokları
    busydatadict = {
        d["userID"]: d
        for doc in db.collection("UserBusyTimes").get()
        for d in [doc.to_dict()]
    }

    # 3) Derslikler
    classroomdatadict = {
        d["ID"]: d
        for doc in db.collection("Classrooms").get()
        for d in [doc.to_dict()]
    }

    # 4) Dersler
    lessondatalist = [doc.to_dict() for doc in db.collection("Lesson").get()]

# ------------------------------ Haftalık tablo şablonu
WEEKDAYS   = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma"]
TIME_SLOTS = [
    "09:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00",
    "13:00-14:00","14:00-15:00","15:00-16:00","16:00-17:00",
    "17:00-18:00","19:00-21:00"
]
ONLINE_ALLOWED = {"17:00-18:00","19:00-21:00"}

def weekly_df():
    df = pd.DataFrame(
        columns=["Gün","Saat","1. Sınıf","2. Sınıf","3. Sınıf","4. Sınıf"],
        dtype=object
    )
    for d in WEEKDAYS:
        for t in TIME_SLOTS:
            df.loc[len(df)] = [d, t, np.nan, np.nan, np.nan, np.nan]
    df.set_index(["Gün","Saat"], inplace=True)
    return df

# İki bölüm için boş şablonlar
dfBLM, dfYZM = weekly_df(), weekly_df()

# ------------------------------ Yerleştirme sırasında kullanılacak haritalar
teacher_names = {}
schedule_busy = defaultdict(set)
room_busy     = defaultdict(set)

# ------------------------------ Esneklik parametreleri
TOL_STEPS = [(0.95,1.15),(0.80,1.30),(0.00,9.99)]
SEG_FUNCS = [
    lambda h: [3]*(h//3) + ([h%3] if h%3 else []),
    lambda h: [2]*(h//2) + ([h%2] if h%2 else []),
    lambda h: [1]*h
]

# ------------------------------ Yardımcı fonksiyonlar
def day_cycle(idx: int):
    return WEEKDAYS[idx % 5:] + WEEKDAYS[:idx % 5]

def lesson_type(ls):
    return "LAB" if "LAB" in ls["lessonName"].upper() else "NORMAL"

def rooms(rtype):
    return [
        info | {"capacity": int(info["capacity"])}
        for info in classroomdatadict.values()
        if info["status"].upper() == rtype
    ]

def pick_room_flexible(cap, desired):
    desired = desired.upper()
    for low, up in TOL_STEPS:
        rng = lambda r: low*cap <= r["capacity"] <= up*cap
        pri = [r for r in rooms(desired) if rng(r)]
        if pri: return random.choice(pri), False
        if desired == "LAB":
            sec = [r for r in rooms("NORMAL") if rng(r)]
            if sec: return random.choice(sec), True
    return None, False

def find_slot(df, col, day, start, hours, tid, online, room_id):
    slots = TIME_SLOTS[start:start+hours] if hours>1 else [TIME_SLOTS[start]]
    if online and not all(s in ONLINE_ALLOWED for s in slots): return False
    if not online and any(s in ONLINE_ALLOWED for s in slots): return False
    if any(pd.notna(df.at[(day,s),col]) for s in slots): return False
    if any((day,s) in schedule_busy[tid] for s in slots): return False
    if room_id and any((day,s) in room_busy[room_id] for s in slots): return False
    return True

def cell_txt(ls, room, note):
    return (
        f"{ls['lessonID']} - {ls['lessonName']} - "
        f"{teacher_names.get(ls['lessonManager'], '')} - {room}"
        + (f"  {note}" if note else "")
    )


def put(df, col, ls, day, start, hours, room_id, note):
    slots = TIME_SLOTS[start:start+hours] if hours>1 else [TIME_SLOTS[start]]
    for s in slots:
        df.at[(day,s),col] = cell_txt(ls, room_id, note)
        schedule_busy[ls["lessonManager"]].add((day,s))
        if room_id != "ONLINE":
            room_busy[room_id].add((day,s))

def undo(df, col, ls):
    mask = df[col].apply(lambda x: isinstance(x,str) and x.split("\n")[0]==ls["lessonID"])
    df.loc[mask, col] = np.nan
    schedule_busy[ls["lessonManager"]] = {
        t for t in schedule_busy[ls["lessonManager"]] if not mask.get(t,False)
    }

# ------------------------------ Yerleştirme işlevleri
def place_contiguous(df, col, ls, segments, online, desired, days_ord):
    for seg in segments:
        placed = False
        for d in days_ord:
            for st in range(len(TIME_SLOTS)-seg+1):
                if online:
                    room_id, note = "ONLINE", None
                else:
                    room, fb = pick_room_flexible(int(ls["lessoncapacity"]), desired)
                    if room is None: return False
                    room_id, note = room["ID"], ("(kapasite nedeniyle)" if fb else None)
                if find_slot(df, col, d, st, seg, ls["lessonManager"], online, room_id):
                    put(df, col, ls, d, st, seg, room_id, note)
                    placed = True
                    break
            if placed: break
        if not placed:
            undo(df, col, ls)
            return False
    return True

def place_noncontiguous(df, col, ls, count, online, desired, days_ord):
    remaining = count
    for d in days_ord:
        for i in range(len(TIME_SLOTS)):
            if remaining == 0: return True
            if online:
                room_id, note = "ONLINE", None
            else:
                room, fb = pick_room_flexible(int(ls["lessoncapacity"]), desired)
                if room is None: return False
                room_id, note = room["ID"], ("(kapasite nedeniyle)" if fb else None)
            if find_slot(df, col, d, i, 1, ls["lessonManager"], online, room_id):
                put(df, col, ls, d, i, 1, room_id, note)
                remaining -= 1
    return remaining == 0

def place_lesson(ls, idx):
    df = dfBLM if ls["sectionID"].upper()=="BLM" else dfYZM
    col = f'{ls["lessonLevel"]}. Sınıf'
    online = ls["lessonstatus"]=="ONLINE"
    desired= lesson_type(ls)
    total  = int(ls["weeklyhour"])
    days_ord = day_cycle(idx)

    for seg_fn in SEG_FUNCS:
        segs = seg_fn(total)
        if place_contiguous(df, col, ls, segs, online, desired, days_ord):
            return True
    return place_noncontiguous(df, col, ls, total, online, desired, days_ord)

def group_by_sync(lst):
    d = defaultdict(list)
    for l in lst:
        key = (
            l["sync_code"]
            if l["sync_code"] != "-"
            else f'__solo__{l["lessonID"]}_{l["sectionID"]}'
        )
        d[key].append(l)
    return list(d.values())

# ------------------------------ Public API fonksiyonları

def create(term: str, scheduleID):
    """
    Term ('bahar' veya 'güz') ve scheduleID alır,
    Firestore’dan veri çeker, yerleştirme yapar ve
    sonuçları Schedule koleksiyonuna yazar.
    """
    getData()  # veri çekmeyi erteledik

    # term filtresi
    if term.lower() == "bahar":
        allowed = {"2","4","6","8"}
    elif term.lower() == "güz":
        allowed = {"1","3","5","7"}
    else:
        raise ValueError("Term must be 'bahar' or 'güz'")

    lessons = [l for l in lessondatalist if l.get("pastyear") in allowed]
    groups  = group_by_sync(lessons)
    sync    = [g for g in groups if g[0]["sync_code"]!="-"]
    solo    = [g[0] for g in groups if g[0]["sync_code"]=="-"]

    sync.sort(key=lambda g: int(g[0]["weeklyhour"]), reverse=True)
    solo.sort(key=lambda l: int(l["weeklyhour"]),   reverse=True)

    for g in sync:
        place_sync_group(g)
    for idx, l in enumerate(solo):
        place_lesson(l, idx)

    dfBLM.fillna("", inplace=True)
    dfYZM.fillna("", inplace=True)

    save_schedule_df(dfBLM, "BLM", scheduleID)
    save_schedule_df(dfYZM, "YZM", scheduleID)


def random_days():
    """
    WEEKDAYS listesini kopyalar, karıştırır ve döner.
    Örnek çıktı: ["Çarşamba","Pazartesi","Cuma","Salı","Perşembe"]
    """
    days = WEEKDAYS[:]   # or days = list(WEEKDAYS)
    random.shuffle(days)
    return days

def place_sync_group(grp):
    """
    Eşzamanlı (sync_code ile gruplanmış) dersleri aynı anda
    uygun bir slot bulunana kadar tekrar tekrar deneyerek yerleştirir.
    """

    cap     = sum(int(g["lessoncapacity"]) for g in grp)
    online  = any(g["lessonstatus"] == "ONLINE" for g in grp)
    desired = "LAB" if any("LAB" in g["lessonName"].upper() for g in grp) else "NORMAL"
    hours   = int(grp[0]["weeklyhour"])

    # 1) Online ise tek blok; değilse oda seçimi once
    if online:
        room_id, note = "ONLINE", None
    else:
        room, fb = pick_room_flexible(cap, desired)
        if room is None:
           
            room, fb = pick_room_flexible(cap, "NORMAL")  
            room_id, note = (room["ID"], "(kapasite nedeniyle)") if room else ("", None)
        else:
            room_id, note = room["ID"], ("(kapasite nedeniyle)" if fb else None)

    # 2) Uygun zaman bulunana kadar döngü
    while True:
        print("n")
        days_ord = random_days()
        for d in days_ord:
            for st in range(len(TIME_SLOTS) - hours + 1):
                slots = TIME_SLOTS[st:st + hours]

                # online/blok kısıtı
                if online:
                    if not all(s in ONLINE_ALLOWED for s in slots):
                        continue
                else:
                    if any(s in ONLINE_ALLOWED for s in slots):
                        continue

                # çakışma kontrolü
                conflict = False
                for g in grp:
                    df  = dfBLM if g["sectionID"].upper() == "BLM" else dfYZM
                    col = f'{g["lessonLevel"]}. Sınıf'
                    if any(pd.notna(df.at[(d,s),col]) for s in slots):
                        conflict = True; break
                    if any((d,s) in schedule_busy[g["lessonManager"]] for s in slots):
                        conflict = True; break
                if conflict or (room_id != "ONLINE" and any((d,s) in room_busy[room_id] for s in slots)):
                    continue

                # bulundu, yerleştir
                for g in grp:
                    df  = dfBLM if g["sectionID"].upper() == "BLM" else dfYZM
                    col = f'{g["lessonLevel"]}. Sınıf'
                    for s in slots:
                        df.at[(d,s),col] = cell_txt(g, room_id, note)
                        schedule_busy[g["lessonManager"]].add((d,s))
                        if room_id != "ONLINE":
                            room_busy[room_id].add((d,s))
                return  # çıkış

        # hiç bulunamadı: bir tur daha döngü (random_days değişecek)
        # Oda da hiç yoksa da room_id="" ile ONLINE gibi davranacak.
def load_schedule_df(schedule_id: str) -> pd.DataFrame:
    """
    Firestore’dan belirli schedule_id ile kaydedilmiş
    tüm satırları okur ve bir DataFrame olarak döner.
    """
    getData()
    df = weekly_df()
    docs = db.collection("Schedule") \
             .where(filter=firestore.FieldFilter("ScheduleID", "==", schedule_id)) \
             .stream()
    for doc in docs:
        d = doc.to_dict()
        day        = d.get("day", "")
        st         = d.get("start_time", "")
        en         = d.get("end_time", "")
        class_col  = d.get("class_column", "1. Sınıf")
        parts      = list(filter(None, [
            d.get("lessonID",""),
            d.get("lessonName",""),
            d.get("lessonManager",""),
            d.get("classroomoflesson","")
        ]))
        df.at[(day,f"{st}-{en}"), class_col] = "\n".join(parts)
    return df.fillna("")

def save_schedule_df(df: pd.DataFrame, section: str, uuid: str) -> str:
    """
    DataFrame’i Schedule koleksiyonuna yazar.
    Returns: oluşturulan schedule_id.
    """
    
    schedule_id = f"{uuid}_{section}"
    batch       = db.batch()
    col         = db.collection("Schedule")

    for (day, time), row in df.iterrows():
        start_time, end_time = time.split("-")
        for class_col, cell in row.dropna().items():
            lines      = str(cell).split("\n")
            lesson_id  = lines[0]
            instructor = lines[2] if len(lines)>2 else ""
            classroom  = lines[3] if len(lines)>3 else ""
            doc_ref    = col.document()
            batch.set(doc_ref, {
                "ScheduleID":        schedule_id,
                "section":           section,
                "lessonID":          lesson_id,
                "lessonManager":     instructor,
                "classroomoflesson": classroom,
                "day":               day,
                "start_time":        start_time,
                "end_time":          end_time,
                "class_column":      class_col,
                "created_at":        datetime.datetime.utcnow(),
                
            })

    batch.commit()
    return schedule_id 


def temizle_key(df: pd.DataFrame, key: str, inplace: bool = False) -> pd.DataFrame:
    """
    Hücrede `key` geçen tüm değerleri tamamen "" ile değiştirir.

    Args:
        df (pd.DataFrame): Herhangi bir DataFrame (MultiIndex de olabilir).
        key (str): Aranacak substring.
        inplace (bool): True ise orijinal df üzerinde değiştirir, 
                        False ise yeni bir DataFrame döner.

    Returns:
        pd.DataFrame: Düzeltilmiş DataFrame.
    """
    def repl(x):
        # Eğer hücre NaN ise olduğu gibi, değilse str(x) içinde key var mı bak
        if pd.notna(x) and key in str(x):
            return ""
        return x

    if inplace:
        # applymap yeni bir df döner, onu tüm hücrelere atıyoruz
        df.iloc[:, :] = df.applymap(repl)
        return df
    else:
        return df.applymap(repl)





