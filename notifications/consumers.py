# from channels.generic.websocket import AsyncJsonWebsocketConsumer

# class NotificationConsumer(AsyncJsonWebsocketConsumer):
# # AsyncWebsocketConsumer degani ham bor, u raw text bilan ishlaydi. Json bilan ishlash uchun bizga buni ishlatish kerak.

#     async def connect(self):
#         user = self.scope["user"]
#         if user.is_anonymous:
#             await self.close()
#         else:
#             self.group_name = f"user_{user.id}"
#             await self.channel_layer.group_add(self.group_name, self.channel_name)
#             await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)

#     async def send_notification(self, event):
#         await self.send_json(event["content"])


from channels.generic.websocket import AsyncJsonWebsocketConsumer
from urllib.parse import parse_qs

class NotificationConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        # Hozircha userni query stringdan olamiz: ws://.../ws/notifications/?user_id=1
        query_string = self.scope["query_string"].decode()  # b"user_id=1" -> "user_id=1"
        params = parse_qs(query_string)
        user_id = params.get("user_id", [None])[0]

        if not user_id:
            await self.close()
            return

        self.user_id = int(user_id)
        self.group_name = f"user_{self.user_id}"

        print("WS CONNECT user_id:", self.user_id)

        # Shu user guruhiga qo'shamiz
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("WS DISCONNECT user_id:", getattr(self, "user_id", None))

    async def send_notification(self, event):
        # event = {"type": "send_notification", "content": {...}}
        print("WS SEND to user_id:", getattr(self, "user_id", None), "event:", event)
        await self.send_json(event["content"])
