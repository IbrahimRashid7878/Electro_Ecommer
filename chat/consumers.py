import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message
from datetime import datetime
from django.db.models import Q

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]

        print("CONNECTED:", self.user)

        if self.user.is_anonymous:
            await self.close()
            return

        self.other_user_id = self.scope['url_route']['kwargs']['user_id']

        self.room_name = f"chat_{min(self.user.id, int(self.other_user_id))}_{max(self.user.id, int(self.other_user_id))}"
        self.room_group_name = f"chat_{self.room_name}"

        print("ROOM:", self.room_group_name)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        print("RECEIVED:", message)

        await self.save_message(self.user.id, self.other_user_id, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': self.user.username,
                'timestamp': datetime.now().strftime("%d %b %Y, %I:%M %p")
            }
        )

    async def chat_message(self, event):
        print("SENDING:", event)

        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def save_message(self, sender_id, receiver_id, message):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=message
        )