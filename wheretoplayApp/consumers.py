from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
import numpy as np
from wheretoplayApp.models import Vote, Workspace, Opportunity

class VotingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.voting_session = self.scope['url_route']['kwargs']['code']
        await self.channel_layer.group_add(
            self.voting_session,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket connection accepted for session: {self.voting_session}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.voting_session, self.channel_name)
        print(f"WebSocket connection closed for session: {self.voting_session}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            vote_info = data.get('votes')
            opportunity_id = data.get('opportunity_id')
            idea_index = data.get('idea_index')
            session_id = data.get('session_id')
            user_id = data.get('user_id')
            guest_id = data.get('guest_id')

            if vote_info and session_id and (user_id or guest_id):
                print(f"Received vote data - Votes: {vote_info}, session_id: {session_id}, user_id: {user_id}, guest_id: {guest_id}, opportunity_id: {opportunity_id}")
                vote_score = vote_info[0]['vote_score']
                criteria_id = vote_info[0]['criteria_id']

                opportunity, threshold = await self.get_opportunity_and_threshold(opportunity_id)
                
                await self.insert_vote(session_id, user_id, guest_id, vote_score, criteria_id, opportunity)

                vote_counts, outlier_user_ids, outlier_guest_ids = await self.get_votes_and_outlier_user_ids(criteria_id, opportunity, threshold)
                print(f"Limits set, outliers calculated. Criteria ID: {criteria_id}, Users: {outlier_user_ids}, Guests: {outlier_guest_ids}")

                # Broadcast the vote to other users in the session
                await self.channel_layer.group_send(
                    self.voting_session,
                    {
                        'type': 'broadcast_protocol',
                        'criteria_id': criteria_id,
                        'idea_index': idea_index,
                        'user_id': user_id,
                        'user_ids': outlier_user_ids,
                        'guest_id': guest_id,
                        'guest_ids': outlier_guest_ids,
                        'result': vote_counts,
                    }
                )
            else:
                print("Missing required fields in received data.")
        except json.JSONDecodeError:
            print("Error decoding JSON data")

    @database_sync_to_async
    def get_opportunity_and_threshold(self, opportunity_id):
        opp = Opportunity.objects.filter(opportunity_id=opportunity_id).first() 
        ws = opp.workspace
        threshold = ws.outlier_threshold
        return opp, threshold

    @database_sync_to_async
    def insert_vote(self, session_id, user_id, guest_id, score, category, opportunity):
        try:
            # opportunity = Opportunity.objects.filter(opportunity_id=opportunity_id).first()

            if opportunity:
                # Create a user vote if the voter is a user and a guest vote if the voter is a guest
                if user_id != None: 
                    Vote.objects.create(
                        opportunity=opportunity,
                        user_id=user_id,
                        vote_score=score,
                        criteria_id=category
                    )
                    print(f"Inserted new vote for user {user_id} in session {session_id}")
                else:
                    Vote.objects.create(
                        opportunity=opportunity,
                        guest_id=guest_id,
                        vote_score=score,
                        criteria_id=category
                    )
                    print(f"Inserted new vote for guest {guest_id} in session {session_id}")
            else:
                print(f"No opportunity found for workspace with code {session_id}")
        except Exception as e:
            print(f"Error inserting or updating vote: {e}")
        
    @database_sync_to_async
    def get_votes_and_outlier_user_ids(self, criteria_id, opportunity, threshold):
        try:
            if not opportunity:
                print(f"No opportunity found")
                return []

            # Get all votes ordered by user_id and latest timestamp
            all_votes = (
                Vote.objects.filter(criteria_id=criteria_id, opportunity=opportunity)
                .order_by("user_id", "-timestamp")  # Order by user_id and most recent timestamp
            )

            vote_counts = [0, 0, 0, 0, 0]

            latest_votes = {}
            latest_guest_votes = {}

            for vote in all_votes:
                if vote.user_id is not None and vote.user_id not in latest_votes:  # Only keep the first (latest) vote for each user
                    latest_votes[vote.user_id] = vote.vote_score
                if vote.user_id is None and vote.guest_id not in latest_guest_votes:
                    latest_guest_votes[vote.guest_id] = vote.vote_score

            for score in latest_votes.values():  # Iterate over the vote scores in the dictionary
                if 1 <= score <= 5:  # Ensure valid vote scores
                    vote_counts[score - 1] += 1

            for score in latest_guest_votes.values():  # Iterate over the vote scores in the dictionary
                if 1 <= score <= 5:  # Ensure valid vote scores
                    vote_counts[score - 1] += 1

            lower_limit, upper_limit = self.mad_outlier_detection(vote_counts, threshold)

            outlier_user_ids = []
            outlier_guest_ids = []

            if lower_limit != None and upper_limit != None:
                # Identify outliers
                for user_id in latest_votes:
                    score = latest_votes[user_id]
                    if score < lower_limit or score > upper_limit:
                        outlier_user_ids.append(user_id)
                
                for guest_id in latest_guest_votes:
                    score = latest_guest_votes[guest_id]
                    if score < lower_limit or score > upper_limit:
                        outlier_guest_ids.append(guest_id)

            return vote_counts, outlier_user_ids, outlier_guest_ids
        
        except Exception as e:
            print(f"Error retrieving votes and outlier user IDs: {e}")
            return []

    def mad_outlier_detection(self, data, threshold):
        if not data:
            return None, None
        
        dataa = []
        for i in range(5):
            for _ in range(data[i]):
                dataa.append(i + 1)

        data_array = np.array(dataa)
        median = np.median(data_array)
        abs_deviation = np.abs(data_array - median)
        mad = np.median(abs_deviation)
        lower_limit = median - (threshold * mad)
        upper_limit = median + (threshold * mad)

        return lower_limit, upper_limit
    
    async def broadcast_protocol(self, event):
        try:
            await self.send(text_data=json.dumps({
                'notification': 'Broadcast results',
                'criteria_id': event['criteria_id'],
                'idea_index': event['idea_index'],
                'user_id': event['user_id'],
                'user_ids': event['user_ids'],
                'guest_id': event['guest_id'],
                'guest_ids': event['guest_ids'],
                'result': event['result'],
            }))
        except Exception as e:
            print(f"Error in broadcast_protocol: {e}")