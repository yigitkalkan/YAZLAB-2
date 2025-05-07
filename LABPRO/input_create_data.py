import pandas as pd

# Excel Dosyasında Bulunan Sütun Başlıkları
sheets = {
    "User Giriş": ["User ID", "Name", "Email", "Rol"],
    "Derslik Giriş": ["Derslik ID", "Kapasite", "Statü"],
    "Ders Tanım": [
        "Ders İsim", 
        "Ders Kodu",
        "Bölüm Kodu", 
        "Haftalık Ders Saati", 
        "Sınıf Seviyesi", 
        "Ders Durumu ONLİNE/YÜZYÜZE",
        "Zorunluluk  ZORUNLU/SEÇMELİ" 
        "Dersi Veren ID",
        "Öğrenci Kapasitesi"
    ],
    "User Meşgül Saatleri":["User","Zaman"]
}

# Excel Dosyası Oluşturma
with pd.ExcelWriter("universiteVerisi.xlsx", engine="openpyxl") as writer:
    for sheet_name, columns in sheets.items():
        df = pd.DataFrame(columns=columns)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
