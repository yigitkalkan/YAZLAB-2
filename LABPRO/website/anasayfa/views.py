from django.shortcuts import render
import DataBaseManager as dt
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http               import JsonResponse

from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect
import pandas as pd
import numpy as np
import json
import re
from programcreator import create,load_schedule_df

dbb = dt.FirebaseManager()



def admin_page(request):

    return render(request,"login_success.html")


def login_page(request):
    if request.method == 'POST':
        username  = request.POST.get('username')
        password  = request.POST.get('password')
        user_type = request.POST.get('user_type')

        if user_type == "admin" and dbb.admin_login_control(username, password, user_type):
            request.session['user_type'] = user_type
            request.session['username']  = username
            return redirect("adminn")

        elif user_type == "öğrenci" and dbb.student_login_control(username, password, user_type):
            student = dbb.studentinfo(username)
            # session’a ekleyelim
            request.session['user_type']     = user_type
            request.session['username']      = student["username"]  # veya username
            request.session['student_level'] = student["studentlevel"]  # yeni eklenen seviye bilgisi
            request.session['section'] = student["studentlevel"]  # yeni eklenen seviye bilgisi
            return redirect('student_dashboard')

        elif user_type == "öğretim görevlisi" and dbb.teacher_login_control(username, password, user_type):
            # Oturuma öğretmen ID'sini yaz
            teacher_id = dbb.teacherEqusername(username)
            request.session['user_type']  = user_type
            request.session['username']   = username
            request.session['teacher_id'] = teacher_id
            return redirect('teacher_dashboard')

        # Hatalı giriş
        return render(request, 'login_page.html', {
            'error': 'Kullanıcı adı, şifre veya tip hatalı.'
        })

    # GET isteği
    return render(request, 'login_page.html')               
            
            

        



def logout_view(request):
    logout(request)
    return redirect("login_page")







@require_POST          # sadece POST kabul
@csrf_protect          # CSRF kontrolü aktif
def add_user(request):
    d = request.POST      
    if dbb.isUser(d["username"]) :
        return  # gelen form alanları
    must = ("userid","username","role","fullname","password")
    if any(not d.get(k) for k in must):
        return JsonResponse({"ok": False, "msg": "Boş alan var!"}, status=400)
    

    
    
    
    dbb.add_user(d["userid"],d["fullname"],d["email"],d["role"],d["username"],d["password"],d["st_class"])
    #                                       –––––––––––––––––––––––––––––––––––––––––––––––

    return JsonResponse({"ok": True})




@require_POST
@csrf_protect
def delete_user(request):
    """Sil düğmesine basıldığında çağrılır – userid POST’ta gelir."""
    uid = request.POST.get("userid")
    if not uid:
        return JsonResponse({"ok": False, "msg": "userid gönderilmedi"}, status=400)

    # ❶ Veritabanından sil (modeline göre düzenle)
    # deleted, _ = User.objects.filter(id=uid).delete()
    # if deleted == 0:
    #     return JsonResponse({"ok": False, "msg": "Kullanıcı bulunamadı"}, status=404)

    
    dbb.delete_user(uid)      # demo logu
    return JsonResponse({"ok": True})



@require_GET
def list_users(request):
    """
    Tüm kullanıcıları JSON olarak döndür.
    Front-end tabloyu her çağrıda bununla tazeler.
    """
    dataa=dbb.userallList()
    
    
    

        # Tabloda gösterilecek isimleri eşleştir
    data = [dict(
            userid   = str(u["UserID"]),
            username = u["username"],
            email    = u["email"],
            role     = u["Role"],
            fullname = u["name"],
            password = u["password"]          # hashed hali; sadece demo!
        ) for u in dataa]
    

    return JsonResponse({"users": data})



@require_GET
def list_managers(request):
    
    qs = dbb.teacheridEqName()

    managers = [
        {
            "id"  : u["UserID"],                                 # int veya UUID
            "name": u["name"]
        }
        for u in qs
    ]

    return JsonResponse({"managers": managers})


def semestertoClassLevel(semester):

    if (semester in ["1","2"]) or (semester in [1,2]):
        return "1"
    elif (semester in ["3","4"]) or (semester in [3,4]):
        return "2"
    elif (semester in ["5","6"]) or (semester in [5,6]):
        return "3"
    elif (semester in ["7","8"]) or (semester in [7,8]):
        return "4"




@require_POST 
@csrf_protect


def add_course(request):

    d = request.POST 
    print(d)
    elective=False
    if d["ctype"]=="Zorunlu":
        elective=False
    else:
        elective=True
    dbb.add_lesson(d["code"],d["dept"],d["name"],semestertoClassLevel(d["semester"]),d["manager"],d["students"],d["hours"],d["status"],elective,d["semester"])
    
    return JsonResponse({"ok": True})


@require_GET
def list_courses(request):
    
    datas,teacherEq=dbb.getCourses()
    output=[]

    for data in datas:
        elective=""
        if data["iselective"]:
            elective="Seçmeli"
        else:
            elective="Zorunlu"

        output.append({

            "code":data["lessonID"],
            "dept": data["sectionID"],
            "name": data["lessonName"],
            "manager": dbb.searchidtoname(teacherEq,data["lessonManager"]),
            "students":data["lessoncapacity"],
            "hours": data["weeklyhour"],
            "semester":data["pastyear"],
            "ctype":elective,
            "status":data["lessonstatus"],
            "sync_code": "" if data["sync_code"]  == "-" else data["sync_code"]
        })
    
    return JsonResponse({"courses": list(output)})


@require_POST            # yalnızca POST kabul et
@csrf_protect            # CSRF koruması (frontend zaten X-CSRFToken gönderiyor)
def delete_course(request):
    """
    AJAX ile gelen 'code' + 'dept' parametrelerine göre dersi siler.
    Beklenen form-data: code=CSE101&dept=CSE
    Dönen JSON:
        {"ok": True}                 – silme başarılı
        {"ok": False, "msg": "..."}  – hata
    """
    code = request.POST.get("code")
    dept = request.POST.get("dept")
    print(code,dept)
    dbb.delete_lesson(code,dept)

    return JsonResponse({"ok": True})

@require_POST
@csrf_protect
def add_classroom(request):
    code     = request.POST.get("code")
    capacity = request.POST.get("capacity")
    status   = request.POST.get("status")
    if not code or not capacity or not status:
        return JsonResponse({"ok": False, "msg": "Eksik parametre"}, status=400)
    
    dbb.add_classroom(code,capacity,status)

    return JsonResponse({"ok": True})

@require_POST
@csrf_protect
def delete_classroom(request):
    code = request.POST.get("code")

    dbb.delete_classroom(code)

    return JsonResponse({"ok": True})

def list_classrooms(request):
    
    datas=dbb.getClassrooms()
    output=[]

    for data in datas:

        output.append({
            "code":data["ID"],
            "capacity":data["capacity"],
            "status" : data["status"]

        })


    
    return JsonResponse({"classrooms": list(output)})




@require_POST
def update_sync_code(request):
    code = request.POST.get("code")
    dept = request.POST.get("dept")
    sync_code = request.POST.get("sync_code", "")
    try:
        
        dbb.sync_code_update(code,dept,sync_code)
        return JsonResponse({"ok": True})
    except :
        return JsonResponse({"ok": False, "msg": "Ders bulunamadı"}, status=404)
    

def temizle_key(df: pd.DataFrame, keys: list[str], inplace: bool = False) -> pd.DataFrame:
    """
    Hücrede keys listesindeki herhangi bir alt stringi barındıranları korur,
    diğer tüm hücreleri "" ile değiştirir.

    Args:
        df (pd.DataFrame): Herhangi bir DataFrame (MultiIndex de olabilir).
        keys (list[str]): Korunacak substrings listesi.
        inplace (bool): True ise orijinal df üzerinde değiştirir,
                        False ise yeni bir DataFrame döner.

    Returns:
        pd.DataFrame: Düzeltilmiş DataFrame.
    """
    def repl(x):
        if pd.isna(x):
            return x
        s = str(x)
        # Eğer s içinde listeden en az bir key varsa orijinali döndür,
        # yoksa boş string
        return x if any(key in s for key in keys) else ""
    
    result = df.applymap(repl)
    if inplace:
        df.iloc[:, :] = result
        return df
    return result

# @login_required
def teacher_dashboard(request):
    # --- Kullanıcı & ID bilgileri ---
    username   = request.session.get('username', request.user.get_username())
    teacher_id = request.session.get('teacher_id')
    print(teacher_id)
    # --- Şu anki schedule ID'sini alın ---
    base_schedule_id = dbb.only_schedule_get()  # örn. "32424"
    
    # BLM ve YZM suffix'li tam ID'leri oluşturuyoruz
    blm_schedule_id = base_schedule_id[0]
    yzm_schedule_id = base_schedule_id[1]

    # --- Öğretmenin derslerini çek ---
    teacherlessons = dbb.teacheroflesson_get(teacher_id)  # liste halinde lessonID'ler
    
    # --- BLM Programı ---
    df_blm = load_schedule_df(blm_schedule_id)
    
    temizle_key(df_blm, teacherlessons, inplace=True)
    
    blm_html = df_blm.to_html(
        classes="table table-bordered text-center",
        na_rep="&nbsp;",
        border=1,
        justify="center"
    )

    # --- YZM Programı ---
    df_yzm = load_schedule_df(yzm_schedule_id)
    
    temizle_key(df_yzm, teacherlessons, inplace=True)
    yzm_html = df_yzm.to_html(
        classes="table table-bordered text-center",
        na_rep="&nbsp;",
        border=1,
        justify="center"
    )

    # --- Meşgul Saat Kaydetme (POST) ---
    if request.method == 'POST':
        day  = request.POST.get('day_of_week')
        slot = request.POST.get('time_slot')
        dbb.save_busy_time(teacher_id, day, slot)
        return redirect('teacher_dashboard')

    # --- Meşgul Saatleri Listele ---
    busy_times = dbb.get_user_busytime(teacher_id)  # [{'day':'Pazartesi','start':'09:00','end':'10:00'}, ...]

    # --- Context Hazırlama ---
    context = {
        'username':      username,
        'teacher_id':    teacher_id,
        'blm_html':      blm_html,
        'yzm_html':      yzm_html,
        'days':          ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma"],
        'times':         [
            "09:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00",
            "13:00-14:00","14:00-15:00","15:00-16:00","16:00-17:00",
            "17:00-18:00","19:00-21:00"
        ],
        'busy_times':    busy_times,
    }
    return render(request, 'teacher_page.html', context)

@require_GET
def student_dashboard(request):
    # Oturumdan kullanıcı ve sınıf bilgisi
    username      = request.session.get('username', request.user.username)
    student_level = request.session.get('student_level')
    print(student_level)
    print(student_level)
    print(student_level)
    print(student_level)
    print(student_level)
    print(student_level)
    print(student_level)
    print(student_level)
    # Varsayalım ki tek bir schedule_id dönen yardımcı fonksiyonunuz var
    base_schedule_id = dbb.only_schedule_get()

    # BLM ve YZM için ayrı ayrı çekiyoruz
    blm_df = load_schedule_df(base_schedule_id[0])
    yzm_df = load_schedule_df(base_schedule_id[1])

    if int(student_level)==1:
        blm_df.drop("2. Sınıf", axis=1, inplace=True)
        blm_df.drop("3. Sınıf", axis=1, inplace=True)
        blm_df.drop("4. Sınıf", axis=1, inplace=True)
        yzm_df.drop("2. Sınıf", axis=1, inplace=True)
        yzm_df.drop("3. Sınıf", axis=1, inplace=True)
        yzm_df.drop("4. Sınıf", axis=1, inplace=True)
    elif int(student_level)==2:
        blm_df.drop("1. Sınıf", axis=1, inplace=True)
        blm_df.drop("3. Sınıf", axis=1, inplace=True)
        blm_df.drop("4. Sınıf", axis=1, inplace=True)
        yzm_df.drop("1. Sınıf", axis=1, inplace=True)
        yzm_df.drop("3. Sınıf", axis=1, inplace=True)
        yzm_df.drop("4. Sınıf", axis=1, inplace=True)
    elif int(student_level)==3:
        blm_df.drop("1. Sınıf", axis=1, inplace=True)
        blm_df.drop("2. Sınıf", axis=1, inplace=True)
        blm_df.drop("4. Sınıf", axis=1, inplace=True)
        yzm_df.drop("1. Sınıf", axis=1, inplace=True)
        yzm_df.drop("2. Sınıf", axis=1, inplace=True)
        yzm_df.drop("4. Sınıf", axis=1, inplace=True)
    elif int(student_level)==4:
        blm_df.drop("1. Sınıf", axis=1, inplace=True)
        blm_df.drop("2. Sınıf", axis=1, inplace=True)
        blm_df.drop("3. Sınıf", axis=1, inplace=True)
        yzm_df.drop("1. Sınıf", axis=1, inplace=True)
        yzm_df.drop("2. Sınıf", axis=1, inplace=True)
        yzm_df.drop("3. Sınıf", axis=1, inplace=True)
    


    # HTML’e çeviriyoruz
    blm_html = blm_df.to_html(
        classes="table table-bordered text-center",
        na_rep="&nbsp;",
        border=1
    )
    yzm_html = yzm_df.to_html(
        classes="table table-bordered text-center",
        na_rep="&nbsp;",
        border=1
    )

    return render(request, 'student_page.html', {
        'username':      username,
        'student_level': student_level,
        'blm_html':      blm_html,
        'yzm_html':      yzm_html,
    })


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
            df.loc[len(df)] = [day, time, "naber", np.nan, np.nan, np.nan]

    # MultiIndex ayarla
    df.set_index(["Gün", "Saat"], inplace=True)

   

    return df


@require_POST
def api_save_busy_time(request):
    # JSON veya form‑data destekler
    data = json.loads(request.body) if request.content_type.startswith('application/json') else request.POST
    tid  = data.get('teacher_id')
    day  = data.get('day_of_week')
    slot = data.get('time_slot')
    
    time=slot.split("-")
    dbb.add_user_busytime(tid,day,time[0],time[1])

    # save_busy_time(tid, day, slot)       # veritabanına kaydet
    return JsonResponse({'status':'success'})


@require_GET
def api_list_busy_times(request):

    tid  = request.session.get('teacher_id')
    
    busy = dbb.get_user_busytime(tid)     # [{'day':'Pazartesi','start':'09:00','end':'10:00'}, ...]
    return JsonResponse({'busy_times': busy})



@require_POST
def api_delete_busy_time(request):
    # Hem JSON hem form‑data kabul et
    data = (json.loads(request.body)
            if request.content_type.startswith('application/json')
            else request.POST)

    tid  = data.get('teacher_id')
    day  = data.get('day_of_week')
    slot = data.get('time_slot')
    if not (tid and day and slot):
        return JsonResponse({'status':'error',
                             'message':'Eksik parametre'}, status=400)
    
    timedata=slot.split("-")

    dbb.delete_user_busytime(tid,day,timedata[0],timedata[1])      # ← kendi silme sorgunuz
    return JsonResponse({'status':'success'})




@require_POST
def api_create_schedule(request):
    """
    POST JSON:
      { "schedule_id": "bazı_id" }
    Yanıt JSON:
      { "status": "success", "schedule_id": "...", "created": true }
      veya
      { "status": "error",   "message": "..." }
    """
    try:
        data = json.loads(request.body)
        sid  = data.get('schedule_id')
        if not sid:
            return JsonResponse({'status':'error','message':'ID giriniz'}, status=400)

        

        create("bahar",sid)
       

        # 3) Başarıyla kaydedildi
        return JsonResponse({
            'status':      'success',
            'schedule_id': sid,
            'created':     True
        })

    except json.JSONDecodeError:
        return JsonResponse({'status':'error','message':'Geçersiz JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status':'error','message': str(e)}, status=500)
    
@require_POST
def api_delete_schedule(request):
    try:
        
        # 1) JSON gövdesini parse et
        data = json.loads(request.body.decode('utf-8'))
        sid  = data.get('schedule_id')
       
        # 2) schedule_id kontrolü
        if not sid:
            return JsonResponse({
                'status': 'error',
                'message': 'ID eksik'
            }, status=400)

        dbb.delete_schedule(sid)

        # 5) Başarılı yanıt
        return JsonResponse({
            'status': 'success',
            
            
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Geçersiz JSON formatı.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_GET

def api_list_schedules(request):
    """
    Veritabanındaki tüm Schedule’ları alır,
    her biri için create_weekly_schedule() ile DataFrame oluşturup HTML’e çevirir,
    ve { status, schedules: [ { id, html } ] } JSON’u döner.
    
    """
    print("calıstı")
    schedules=dbb.getschedulesList()
    result = []

    for schedname in schedules:
        # Bazı kullanıcılar, DataFrame'i entry'lere göre doldurmak isteyebilir:
        # df = fill_df_from_entries(create_weekly_schedule(), sched.entries.all())
        # ama biz boş tablo kullanacağız:
        df_html = load_schedule_df(schedname).to_html(
            classes="table table-bordered text-center",
            na_rep="&nbsp;",
            border=1
        )
        result.append({
            'id':   schedname,
            'html': df_html
        })

    return JsonResponse({
        'status':    'success',
        'schedules': result
    })





@require_POST
def api_select_schedule(request):
    data = json.loads(request.body)
    sid = data.get('schedule_id')
    sel = data.get('selected')  # true/false

    if not sid or sel is None:
        return JsonResponse({'status':'error','message':'Eksik parametre'}, status=400)

    # session’da bir liste tutmak isterseniz:
    sel_list = request.session.get('selected_schedules', [])
    if sel and sid not in sel_list:
        sel_list.append(sid)
    if not sel and sid in sel_list:
        sel_list.remove(sid)
    request.session['selected_schedules'] = sel_list

    return JsonResponse({'status':'success','selected_schedules': sel_list})