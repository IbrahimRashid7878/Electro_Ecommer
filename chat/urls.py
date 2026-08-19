from django.urls import path
from . import views

urlpatterns = [
    # User chat page
    path('chat/', views.user_chat, name='user_chat'),

    # Admin inbox (list of users)
    path('admin/inbox/', views.admin_inbox, name='admin_inbox'),

    # Admin chatting with specific user
    path('admin/chat/<int:user_id>/', views.admin_chat, name='admin_chat'),
    
]