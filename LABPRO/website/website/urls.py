"""
URL configuration for website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from anasayfa import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('adminn/', views.admin_page, name='adminn'),
    path('', views.login_page,name="login_page"),
    path("", views.logout, name="logout"),
    path("api/add-user/", views.add_user, name="add_user"),
    path("api/delete-user/", views.delete_user, name="delete_user"),
    path("api/list-users/",  views.list_users,  name="list_users"),
    path("api/list-managers/", views.list_managers, name="list_managers"),
    path("api/add-course/",  views.add_course,  name="add_course"),
    path("api/list-courses/", views.list_courses, name="list_courses"),
    path("api/delete-course/", views.delete_course, name="delete_course"),
      path("api/list-classrooms/",  views.list_classrooms,  name="list_classrooms"),
    path("api/add-classroom/",    views.add_classroom,    name="add_classroom"),
    path("api/delete-classroom/", views.delete_classroom, name="delete_classroom"),
    path("api/update-sync-code/", views.update_sync_code, name="update_sync_code"),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('api/save-busy-time/', views.api_save_busy_time, name='api_save_busy_time'),
    path('api/list-busy-times/', views.api_list_busy_times, name='api_list_busy_times'),
    path('api/delete-busy-time/', views.api_delete_busy_time,
         name='api_delete_busy_time'),


    path('api/create-schedule/',   views.api_create_schedule,   name='api_create_schedule'),
    path('api/delete-schedule/',   views.api_delete_schedule,   name='api_delete_schedule'),
     path(
        'api/list-schedules/',
        views.api_list_schedules,
        name='api_list_schedules'
    ),
    path('api/select_schedule/', views.api_select_schedule, name='api_select_schedule'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard')
]
