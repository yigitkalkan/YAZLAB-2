import firebase_admin
from firebase_admin import credentials,firestore
import sys
import json
cred = credentials.Certificate("ServiceKeyvuzok.json")
firebase_admin.initialize_app(cred)


dataBaseFireBase = firestore.client()








class FirebaseManager():


    def delete_user(self,id):

        controlref=dataBaseFireBase.collection("Users").where(filter=firestore.FieldFilter("UserID","==",id)).get()

        for doc in controlref:
            docref=dataBaseFireBase.collection("Users").document(doc.id)
            data=doc.to_dict()
            docref.delete()

            if data["Role"]=="öğretim görevlisi":
                
                docref=dataBaseFireBase.collection("UserBusyTimes").where(filter=firestore.FieldFilter("userID","==",id)).get()
                
                for doc in docref:
                    docref=dataBaseFireBase.collection("UserBusyTimes").document(doc.id)
                    docref.delete()



        
        


        
    
    def add_user(self,ID,name,email,role,username,password,level="-"):

        controlref=dataBaseFireBase.collection("Users").where(filter=firestore.FieldFilter("UserID","==",ID)).get()
        if any(controlref):
            return

        docref=dataBaseFireBase.collection("Users").document()

        docref.set({"UserID":ID,
                    "Role":role,
                    "name":name,
                    "email":email,
                    "username":username,
                    "password":password,
                    "studentlevel":level})
        
        if role=="öğretim görevlisi":

            docref=dataBaseFireBase.collection("UserBusyTimes").document()
            docref.set({

                "userID":ID,
                "times":[]

            })

            
        
    def add_classroom(self,ID,capacity,status):

        controlref=dataBaseFireBase.collection("Classrooms").where(filter=firestore.FieldFilter("ID","==",ID)).get()
        if any(controlref):
            return

        docref=dataBaseFireBase.collection("Classrooms").document()
        docref.set({"ID":ID,
                    "capacity":capacity,
                    "status":status})

    def add_user_busytime(self,userID,day,startTime,endTime):
        controlref=dataBaseFireBase.collection("UserBusyTimes").where(filter=firestore.FieldFilter("userID","==",userID)).get()
        data=day+","+startTime+","+endTime
        if not any(controlref):
            
            docref=dataBaseFireBase.collection("UserBusyTimes").document()
            docref.set({"userID":userID,
                        "times":[data]})
        else:
            busytimes=[]
            for doc in controlref:
                busytimes=doc.to_dict()["times"]
                busytimes.append(data)
                controlref=dataBaseFireBase.collection("UserBusyTimes").document(doc.id)
                controlref.set({"userID":userID,
                                "times":busytimes})
    
    def get_user_busytime(self,Id):
        output=[]
        doc=dataBaseFireBase.collection("UserBusyTimes").where(filter=firestore.FieldFilter("userID","==",Id)).get()
        for document in doc:
            data=document.to_dict()
            datatimeslist=data["times"]
            for times in datatimeslist:
                data=times.split(",")
                output.append({
                "day":data[0],
                "start":data[1],
                "end":data[2]

            })
        return output


    def delete_user_busytime(self,Id,day,start,end):
        doc=dataBaseFireBase.collection("UserBusyTimes").where(filter=firestore.FieldFilter("userID","==",Id)).get()
        removeddata=day+","+start+","+end

        for document in doc:
            docref=dataBaseFireBase.collection("UserBusyTimes").document(document.id)
            removedlist=document.to_dict()["times"]
            print(removedlist)
            print(removeddata)
            removedlist.remove(removeddata)
            docref.set({
                "times":removedlist
            },merge=True)



    def add_lesson(self,lessonID,sectionID,name,lessonLevel,LessonManager,lessoncapacity,weeklyhour,status,isElective,pastyear):

        controlref=dataBaseFireBase.collection("Lesson").where(filter=firestore.FieldFilter("lessonID","==",lessonID)).where(filter=firestore.FieldFilter("sectionID","==",sectionID)).get()
        if any(controlref):
            return

        docref=dataBaseFireBase.collection("Lesson").document()
        docref.set({"lessonID":lessonID,
                   "sectionID":sectionID,
                     "lessonName":name,
                     "lessonManager":LessonManager,
                     "lessonstatus":status,
                     "iselective":isElective,
                     "lessoncapacity":lessoncapacity,
                     "weeklyhour":weeklyhour,
                    "pastyear":pastyear,
                    "lessonLevel":lessonLevel,
                    "sync_code":"-"})
        
        sections=sectionID.split(",")

        if isElective:
            if len(sections)>1:
                for section in sections:

                    if lessonLevel=="1":
                        self.OneLessonAdd(section,lessonID)
                    elif lessonLevel=="2":
                        self.TwoLessonAdd(section,lessonID)
                    elif lessonLevel=="3":
                        self.ThreeLessonAdd(section,lessonID)
                    elif lessonLevel=="4":
                        self.FourLessonAdd(section,lessonID)                    

            else:
                if lessonLevel=="1":
                    self.OneLessonAdd(sectionID,lessonID)
                elif lessonLevel=="2":
                    self.TwoLessonAdd(sectionID,lessonID)
                elif lessonLevel=="3":
                    self.ThreeLessonAdd(sectionID,lessonID)
                elif lessonLevel=="4":
                    self.FourLessonAdd(sectionID,lessonID)  
        else:
            if lessonLevel=="1":
                self.OneLessonAdd(sectionID,lessonID)
            elif lessonLevel=="2":
                self.TwoLessonAdd(sectionID,lessonID)
            elif lessonLevel=="3":
                self.ThreeLessonAdd(sectionID,lessonID)
            elif lessonLevel=="4":
                self.FourLessonAdd(sectionID,lessonID)  



    def OneLessonAdd(self,sectionID,lessoncode):
        controlref=dataBaseFireBase.collection("OneClass").where(filter=firestore.FieldFilter("sectionID","==",sectionID)).get()
        if not any(controlref):
            docref=dataBaseFireBase.collection("OneClass").document()
            docref.set({"sectionID":sectionID,
                        "lesson_codes":[lessoncode]})
            return
                   
        docs=dataBaseFireBase.collection("OneClass").where(filter=firestore.FieldFilter("sectionID","==",sectionID)).get()
        for doc in docs:

            data=doc.to_dict()
            
            lessons:list=data["lesson_codes"]
            lessons.append(lessoncode)

            docref=dataBaseFireBase.collection("OneClass").document(doc.id)
            docref.set({
                "sectionID":data["sectionID"],
                "lesson_codes":lessons

            })

    def TwoLessonAdd(self,sectionID,lessoncode):

        controlref=dataBaseFireBase.collection("TwoClass").where(filter=firestore.FieldFilter("sectionID","==",sectionID)).get()
        if not any(controlref):
            docref=dataBaseFireBase.collection("TwoClass").document()
            docref.set({"sectionID":sectionID,
                        "lesson_codes":[lessoncode]})
            return
        docs=dataBaseFireBase.collection("TwoClass").where(filter=firestore.FieldFilter("sectionID","==",sectionID)).get()
        for doc in docs:

            data=doc.to_dict()
            
            lessons:list=data["lesson_codes"]
            lessons.append(lessoncode)

            docref=dataBaseFireBase.collection("TwoClass").document(doc.id)
            docref.set({
                "sectionID":data["sectionID"],
                "lesson_codes":lessons

            })

    def ThreeLessonAdd(self,sectionID,lessoncode):

        controlref=dataBaseFireBase.collection("ThreeClass").where(filter=firestore.FieldFilter("sectionID","==",sectionID)).get()
        if not any(controlref):
            docref=dataBaseFireBase.collection("ThreeClass").document()
            docref.set({"sectionID":sectionID,
                        "lesson_codes":[lessoncode]})
            return
        docs=dataBaseFireBase.collection("ThreeClass").where(filter=firestore.FieldFilter("sectionID","==",sectionID)).get()
        for doc in docs:

            data=doc.to_dict()
            
            lessons:list=data["lesson_codes"]
            lessons.append(lessoncode)

            docref=dataBaseFireBase.collection("ThreeClass").document(doc.id)
            docref.set({
                "sectionID":data["sectionID"],
                "lesson_codes":lessons

            })

    def FourLessonAdd(self,sectionID,lessoncode):
        controlref=dataBaseFireBase.collection("FourClass").where(filter=firestore.FieldFilter("sectionID","==",sectionID)).get()
        if not any(controlref):
            docref=dataBaseFireBase.collection("FourClass").document()
            docref.set({"sectionID":sectionID,
                        "lesson_codes":[lessoncode]})
            return
        docs=dataBaseFireBase.collection("FourClass").where(filter=firestore.FieldFilter("sectionID","==",sectionID)).get()
        for doc in docs:

            data=doc.to_dict()
            
            lessons:list=data["lesson_codes"]
            lessons.append(lessoncode)

            docref=dataBaseFireBase.collection("FourClass").document(doc.id)
            docref.set({
                "sectionID":data["sectionID"],
                "lesson_codes":lessons

            })




    def is_time_overlapping(self,range1, range2):
        def time_to_minutes(time_str):
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes

        day1, start1, end1 = range1
        day2, start2, end2 = range2

        if day1 != day2:
            return False  

        start1, end1 = time_to_minutes(start1), time_to_minutes(end1)
        start2, end2 = time_to_minutes(start2), time_to_minutes(end2)

    
        if start1 == start2 and end1 == end2:
            return True

        return (start1 < start2 < end1) or (start1 < end2 < end1) or (start2 < start1 < end2)



    def databaseClear(self):

        self.__delete_all_collections()





    def __delete_all_collections(self):
        collections = dataBaseFireBase.collections()
        for collection in collections:
            self.__delete_collection(collection)

    def __delete_collection(collection_ref):
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()
            
    def admin_login_control(self,username,password,usertype):
        
        if usertype=="admin":
            print("admin secildi")
            docdata=dataBaseFireBase.collection("Users").where(filter=firestore.FieldFilter("username","==",username)).where(filter=firestore.FieldFilter("password","==",password)).get()

            if not docdata:
                print("hatalı durum")
                return False
            else:
                print("hatasız")
                return True
    def student_login_control(self,username,password,usertype):


        if usertype=="öğrenci":

            docdata=dataBaseFireBase.collection("Users").where(filter=firestore.FieldFilter("username","==",username)).where(filter=firestore.FieldFilter("password","==",password)).where(filter=firestore.FieldFilter("Role","==","öğrenci")).get()
            if not docdata:
                return False
            else:
                return True
            

    def teacher_login_control(self,username,password,usertype):
        if usertype=="öğretim görevlisi":
            print("giriss")

            docdata=dataBaseFireBase.collection("Users").where(filter=firestore.FieldFilter("username","==",username)).where(filter=firestore.FieldFilter("password","==",password)).where(filter=firestore.FieldFilter("Role","==","öğretim görevlisi")).get()
            if not docdata:
                return False
            else:
                return True

    def userallList(self):

        data=[]
        dd=dataBaseFireBase.collection("Users").get()
        for ii in dd:
            data.append(ii.to_dict())

        return data


    def teacheridEqName(self):
        
        datas=self.userallList()
        output=[]
        for data in datas:

            if data["Role"]=='öğretim görevlisi':
                output.append({"UserID":data["UserID"],"name":data["name"]})

        return output

    def getCourses(self):

        docdata=dataBaseFireBase.collection("Lesson").get()
        output=[]
        for data in docdata:

            
            output.append(data.to_dict())


        return (output,self.teacheridEqName())


    def getClassrooms(self):

        docdata=dataBaseFireBase.collection("Classrooms").get()
        output=[]

        for data in docdata:

            output.append(data.to_dict())



        return output


    def searchidtoname(self,data,key):

        for value in data:

            if value["UserID"]==key:
                return value["name"]
            


    def delete_lesson(self,lessoncode,sectioncode):

        lessondata=dataBaseFireBase.collection("Lesson").where(filter=firestore.FieldFilter("lessonID","==",lessoncode)).where(filter=firestore.FieldFilter("sectionID","==",sectioncode)).get()
        lessonlevel=""
        for data in lessondata:
            veri=data.to_dict()
            docref=dataBaseFireBase.collection("Lesson").document(data.id)
            docref.delete()
            if veri["lessonLevel"]=="1":
                lessonlevel="OneClass"
            elif veri["lessonLevel"]=="2":
                lessonlevel="TwoClass"
            elif veri["lessonLevel"]=="3":
                lessonlevel="ThreeClass"
            else:
                lessonlevel="FourClass"




        


        secitondata=dataBaseFireBase.collection(lessonlevel).where(filter=firestore.FieldFilter("sectionID","==",sectioncode)).get()

        for data in secitondata:
            docref=dataBaseFireBase.collection(lessonlevel).document(data.id)
            datalist=data.to_dict()["lesson_codes"]
            datalist.remove(lessoncode)

            docref.set({
                "lesson_codes": datalist
            },merge=True)


    def delete_classroom(self,ID):

        docdata=dataBaseFireBase.collection("Classrooms").where(filter=firestore.FieldFilter("ID","==",ID)).get()

        for data in docdata:

            docref=dataBaseFireBase.collection("Classrooms").document(data.id)

            docref.delete()

        
    def sync_code_update(self,code,dept,newtext):


        docdata=dataBaseFireBase.collection("Lesson").where(filter=firestore.FieldFilter("lessonID","==",code)).where(filter=firestore.FieldFilter("sectionID","==",dept)).get()

        for doc in docdata:
            docre=dataBaseFireBase.collection("Lesson").document(doc.id)
            docre.set({
                "sync_code": "-" if newtext == "" else newtext
            },merge=True)

    def teacherEqusername(self,username):

        docdata=dataBaseFireBase.collection("Users").where(filter=firestore.FieldFilter("username","==",username)).get()

        for doc in docdata:
            data=doc.to_dict()

            return data["UserID"]

    def getschedulesList(self):
        docdata=dataBaseFireBase.collection("Schedule").get()

        schedulesList=[]
        for doc in docdata:
            data=doc.to_dict()

            schedulesList.append(data["ScheduleID"])


        return list(set(schedulesList))

    def delete_schedule(self,id:str):
        
        if "BLM" in id:
            batch=dataBaseFireBase.batch()
            docrefBLM=dataBaseFireBase.collection("Schedule").where(filter=firestore.FieldFilter("ScheduleID","==",id)).get()
            docrefYZM=dataBaseFireBase.collection("Schedule").where(filter=firestore.FieldFilter("ScheduleID","==",id.replace("BLM","YZM"))).get()

            for doc in docrefBLM:
                docreBLM=dataBaseFireBase.collection("Schedule").document(doc.id)
                batch.delete(docreBLM)
            for doc in docrefYZM:
                docreYZM=dataBaseFireBase.collection("Schedule").document(doc.id)
                batch.delete(docreYZM)
            batch.commit()
        if "YZM" in id:
            batch=dataBaseFireBase.batch()
            docrefBLM=dataBaseFireBase.collection("Schedule").where(filter=firestore.FieldFilter("ScheduleID","==",id.replace("YZM","BLM"))).get()
            docrefYZM=dataBaseFireBase.collection("Schedule").where(filter=firestore.FieldFilter("ScheduleID","==",id)).get()            
            
            for doc in docrefBLM:
                docreBLM=dataBaseFireBase.collection("Schedule").document(doc.id)
                batch.delete(docreBLM)
            for doc in docrefYZM:
                docreYZM=dataBaseFireBase.collection("Schedule").document(doc.id)
                batch.delete(docreYZM)
            batch.commit()


    def only_schedule_get(self):

        data=dataBaseFireBase.collection("Schedule").get()
        output=[]
        outputt=["",""]
        for doc in data:
            dataa=doc.to_dict()

            output.append(dataa["ScheduleID"])

        
        for lesson in list(set(output)):

            if "BLM" in lesson:
                outputt[0]=lesson

            if "YZM" in lesson:
                outputt[1]=lesson

        return outputt

        
    def teacheroflesson_get(self,id):
        data=dataBaseFireBase.collection("Lesson").where(filter=firestore.FieldFilter("lessonManager","==",id)).get()
        output=[]
        for doc in data:
            veri=doc.to_dict()
            output.append(veri["lessonID"])
        return output

    def studentinfo(self,username):
        data=dataBaseFireBase.collection("Users").where(filter=firestore.FieldFilter("username","==",username)).get()


        for doc in data:
            dataa=doc.to_dict()
            return dataa
        
    def isUser(self,id):
        control=dataBaseFireBase.collection("Users").where(filter=firestore.FieldFilter("username","==",id)).get()

        for doc in control:

            return True
            
        return False
        
 
        



















        


