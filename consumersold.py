from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
from wheretoplayApp.models import Vote

class VotingConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            print(f"Received data from frontend: {data}")  # Debug: Print the entire received data
            
            votes = data.get("votes", [])
            voting_session_id = data.get("voting_session_id")
            user_id = data.get("user_id")

            # Check if the main required fields are present
            if not voting_session_id or not user_id:
                await self.send(text_data=json.dumps({
                    'message': 'Missing voting_session_id or user_id'
                }))
                return

            # Process each vote entry
            for vote in votes:
                criteria_id = vote.get("criteria_id")
                vote_score = vote.get("vote_score")
                
                # Additional debug prints
                print(f"Processing vote - Criteria ID: {criteria_id}, Vote Score: {vote_score}")

                # Check for each individual vote data integrity
                if criteria_id is None or vote_score is None:
                    await self.send(text_data=json.dumps({
                        'message': 'Missing required fields in vote data'
                    }))
                    return
                
                # Save vote to the database using sync_to_async
                await sync_to_async(Vote.objects.create)(
                    voting_session_id=voting_session_id,
                    user_id=user_id,
                    vote_score=vote_score,
                    criteria_id=criteria_id
                )

            await self.send(text_data=json.dumps({'message': 'Votes saved successfully!'}))

        except Exception as e:
            print(f"Error saving data to database: {e}")
            await self.send(text_data=json.dumps({'message': 'Error saving vote data'}))
