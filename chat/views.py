from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()


# @login_required
# def admin_chat(request, user_id):
#     # Optional: restrict only admin/staff
#     # if not request.user.is_staff:
#     #     return render(request, "403.html") 
#     return render(request, "admin_chat.html", {
#         "user_id": user_id
#     })


def admin_chat(request, user_id):

    
    admin = request.user

    messages = Message.objects.filter(
        Q(sender=admin, receiver_id=user_id) |
        Q(sender_id=user_id, receiver=admin)
    ).order_by('timestamp')

    return render(request, "admin_chat.html", {
        "user_id": user_id,
        "messages": messages
    })

# @login_required
def admin_inbox(request):
    # if not request.user.is_staff:
    #     return HttpResponse("Unauthorized access is not allowed.", status=401)

    admin = request.user

    messages = Message.objects.filter(
        Q(sender=admin) | Q(receiver=admin)
    ).order_by('-timestamp')

    print("TOTAL MESSAGES:", messages.count())

    inbox = {}

    for msg in messages:
        if msg.sender_id == admin.id:
            other = msg.receiver
        else:
            other = msg.sender

        if other.id not in inbox:
            inbox[other.id] = {
                "user": other,
                "last_msg": msg.content,
                "time": msg.timestamp
            }

    user_list = list(inbox.values())

    print("INBOX USERS:", len(user_list))

    return render(request, "admin_inbox.html", {
        "user_list": user_list
    })

def user_chat(request):
    admin_id = 1 

    messages = Message.objects.filter(
        Q(sender=request.user, receiver_id=admin_id) |
        Q(sender_id=admin_id, receiver=request.user)
    ).order_by('timestamp')

    return render(request, "user_chat.html", {
        "messages": messages
    })


