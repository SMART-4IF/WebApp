import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(self.scope)
        self.room_name = self.scope['path'].replace('/visio_conference/', '')
        self.room_group_name = 'room_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print('Disconnected')

    async def receive(self, text_data):
        receive_json = json.loads(text_data)
        message = receive_json['message']
        action = receive_json['action']

        if(action == 'new-offer') or (action == 'new-answer'):
            receiver_channel_name = receive_json['message']['receiver_channel_name']

            receive_json['message']['receiver_channel_name'] = self.channel_name

            await self.channel_layer.send(
                receiver_channel_name,
                {
                    'type': 'send.sdp',
                    'receive_json': receive_json
                }
            )

            return

        receive_json['message']['receiver_channel_name'] = self.channel_name

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send.sdp',
                'receive_json': receive_json
            }
        )

    async def send_sdp(self, event):
        receive_json = event['receive_json']
        await self.send(text_data=json.dumps(receive_json))
