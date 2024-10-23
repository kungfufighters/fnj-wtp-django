from channels.generic.websocket import AsyncWebsocketConsumer
import json

class VotingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            # Parse the JSON data
            data = json.loads(text_data)
            
            # Extract the 'ideaIndex' and 'votes' from the incoming data
            idea_index = data.get('ideaIndex', None)  # If the key is missing, it will return None
            votes = data.get('votes', None)  # If the key is missing, it will return None

            # Log the received values
            print(f"Received vote data - Idea Index: {idea_index}, Votes: {votes}")
            
            # Send a simple confirmation message back to the frontend
            await self.send(text_data=json.dumps({
                'message': 'received!'
            }))
        except json.JSONDecodeError:
            print("Error decoding JSON data")
