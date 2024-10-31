from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
import random

class VotingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.voting_session = '12345' # must be a valid unicode string with length < 100
        await self.channel_layer.group_add(
            self.voting_session,
            self.channel_name
        )
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
            session_id = data.get('session_id', None)  # If the key is missing, it will return None
            user_id = data.get('user_id', None)  # If the key is missing, it will return None

            # Log the received values
            print(f"Received vote data - Idea Index: {idea_index}, Votes: {votes}, session_id: {session_id}, user_id: {user_id}")

            # Insert the new vote into the database
            await self.insert_vote(session_id, user_id, votes[0]['vote_score'], votes[0]['criteria_id'])

            # Alert all consumers about the new votes and if they are an outlier
            await self.channel_layer.group_send(
                self.voting_session,
                {
                    'type': 'broadcast_protocol',
                    'criteria_id': votes[0]['criteria_id'],
                    'vote_score': votes[0]['vote_score'],
                    'session_id': session_id,
                    'user_id': user_id,
                }
            )

        except json.JSONDecodeError:
            print("Error decoding JSON data")


    # TO BE IMPLEMENTED
    # Insert the vote into the datbase
    @database_sync_to_async
    def insert_vote(self, session_id, user_id, score, category):
        pass

    # TO BE IMPLEMENTED 
    # 1. replace votes with the actual votes for this opportunity by querying the database
    # 2. replace isOutlier with whether this users current vote s an outlier based on gustavo's function
    # @database_sync_to_async
    async def broadcast_protocol(self, event):
        votes = []
        for i in range(6):
            miniVotes = [0, 0, 0, 0, 0]
            for j in range(8):
                miniVotes[random.randint(0, 4)]+=1
            votes.append(miniVotes)

        # -1 = not an outlier, otherwise they are an outlier in the category given by criteria id
        outlierNum = -1 if random.randint(0, 100) > 50 else event['criteria_id']

        await self.send(text_data=json.dumps({
            'result': votes,
            'outlier': outlierNum,
        }))
        
    # TO BE IMPLEMENTED 
    @database_sync_to_async 
    def outlier_notification(self, event):
        pass


    

