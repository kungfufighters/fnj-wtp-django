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
            votes = data.get('votes')
            opportunity_id = data.get('opportunity_id')
            session_id = data.get('session_id')
            user_id = data.get('user_id')
            guest_id = data.get('guest_id')
            curVotes = data.get('curVotes')

            if votes and session_id and (user_id or guest_id):
                print(f"Received vote data - Votes: {votes}, session_id: {session_id}, user_id: {user_id}, guest_id: {guest_id}, opportunity_id: {opportunity_id}")
                vote_score = votes[0]['vote_score']
                criteria_id = votes[0]['criteria_id']
                
                await self.insert_vote(session_id, user_id, guest_id, vote_score, criteria_id, opportunity_id)
                
                # Fetch updated votes to check for outliers
                # current_votes = await self.get_votes(criteria_id, session_id, opportunity_id)
                
                limits = await self.mad_outlier_detection(curVotes, opportunity_id)
                lower = limits[0]
                upper = limits[1]

                if limits:
                    outlier_ids = await self.get_outlier_user_ids(criteria_id, opportunity_id, lower, upper)
                    outlier_user_ids = outlier_ids[0]
                    outlier_guest_ids = outlier_ids[1]
                    print(f"Limits set, outliers calculated. Criteria ID: {criteria_id}, Users: {outlier_user_ids}")
                    await self.channel_layer.group_send(
                        self.voting_session,
                        {
                            'type': 'send_limits',
                            'criteria_id': criteria_id,
                            'user_id': user_id,
                            'guest_id': guest_id,
                            'user_ids': outlier_user_ids,
                            'guest_ids': outlier_guest_ids,
                            'lower': lower,
                            'upper': upper,
                        })
                else:
                    print("Limits not set.")

                # Broadcast the vote to other users in the session
                await self.channel_layer.group_send(
                    self.voting_session,
                    {
                        'type': 'broadcast_protocol',
                        'criteria_id': criteria_id,
                        'vote_score': vote_score,
                        'session_id': session_id,
                        'user_id': user_id,
                        'guest_id': guest_id,
                        'opportunity_id': opportunity_id,
                        'curVotes': curVotes,
                    }
                )
            else:
                print("Missing required fields in received data.")
        except json.JSONDecodeError:
            print("Error decoding JSON data")

    @database_sync_to_async
    def insert_vote(self, session_id, user_id, guest_id, score, category, opportunity_id):
        try:
            opportunity = Opportunity.objects.filter(opportunity_id=opportunity_id).first()

            if opportunity:
                # Create a user vote if the voter is a user and a guest vote if the voter is a guest
                if user_id != None: 
                    Vote.objects.create(
                        opportunity=opportunity,
                        user_id=user_id,
                        vote_score=score,
                        criteria_id=category
                    )
                else:
                    Vote.objects.create(
                        opportunity=opportunity,
                        guest_id=guest_id,
                        vote_score=score,
                        criteria_id=category
                    )
                print(f"Inserted new vote for user {user_id} in session {session_id}")
            else:
                print(f"No opportunity found for workspace with code {session_id}")
        except Exception as e:
            print(f"Error inserting or updating vote: {e}")

    @database_sync_to_async
    def get_votes(self, criteria_id, session_id, opportunity_id):
        try:
            opportunity = Opportunity.objects.filter(opportunity_id=opportunity_id).first()
            all_votes = (
                Vote.objects.filter(criteria_id=criteria_id, opportunity=opportunity)
                .order_by("user_id", "-timestamp")  # Order by user_id and most recent timestamp
            )

            latest_votes = {}
            latest_guest_votes = {}
            for vote in all_votes:
                if vote.user_id is not None and vote.user_id not in latest_votes:  # Only keep the first (latest) vote for each user_id
                    latest_votes[vote.user_id] = vote.vote_score
                if vote.user_id is None and vote.guest_id not in latest_guest_votes:
                    latest_guest_votes[vote.guest_id] = vote.vote_score


            vote_counts = [0, 0, 0, 0, 0]

            for score in latest_votes.values():  # Iterate over the vote scores in the dictionary
                if 1 <= score <= 5:  # Ensure valid vote scores
                    vote_counts[score - 1] += 1

            for score in latest_guest_votes.values():  # Iterate over the vote scores in the dictionary
                if 1 <= score <= 5:  # Ensure valid vote scores
                    vote_counts[score - 1] += 1

            print(f"Vote counts for criteria {criteria_id} in session {session_id}: {vote_counts}")
            return vote_counts
        
        except Exception as e:
            print(f"Error retrieving votes: {e}")
            return [0, 0, 0, 0, 0]
        
    @database_sync_to_async
    def get_outlier_user_ids(self, criteria_id, opportunity_id, lower_limit, upper_limit):
        try:
            opportunity = Opportunity.objects.filter(opportunity_id=opportunity_id).first()
            if not opportunity:
                print(f"No opportunity found for ID {opportunity_id}")
                return []

            # Get all votes ordered by user_id and latest timestamp
            all_votes = (
                Vote.objects.filter(criteria_id=criteria_id, opportunity=opportunity)
                .order_by("user_id", "-timestamp")  # Order by user_id and most recent timestamp
            )

            # Get the latest vote for each user
            latest_votes = {}
            latest_guest_votes = {}
            for vote in all_votes:
                if vote.user_id is not None and vote.user_id not in latest_votes:  # Only keep the first (latest) vote for each user
                    latest_votes[vote.user_id] = vote.vote_score
                if vote.user_id is None and vote.guest_id not in latest_guest_votes:
                    latest_guest_votes[vote.guest_id] = vote.vote_score


            # Identify outliers
            outlier_user_ids = [
                user_id for user_id, score in latest_votes.items() if score < lower_limit or score > upper_limit
            ]

            outlier_guest_ids = [
                guest_id for guest_id, score in latest_guest_votes.items() if score < lower_limit or score > upper_limit
            ]

            return (outlier_user_ids, outlier_guest_ids)
        
        except Exception as e:
            print(f"Error retrieving outlier user IDs: {e}")
            return []

    @database_sync_to_async
    def mad_outlier_detection(self, data, opportunity_id):
        if not data:
            return False
        
        opp = Opportunity.objects.filter(opportunity_id=opportunity_id).first()
        ws = opp.workspace
        threshold = ws.outlier_threshold
        
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

        return (lower_limit, upper_limit, median)


    async def broadcast_protocol(self, event):
        try:
            # votes = await self.get_votes(event['criteria_id'], event['session_id'], event['opportunity_id'])
            await self.send(text_data=json.dumps({
                'notification': 'Broadcast results',
                'result': event['curVotes'],
                'criteria_id': event['criteria_id']
            }))
            #print(f"Broadcasted votes for criteria {event['criteria_id']}")
        except Exception as e:
            print(f"Error in broadcast_protocol: {e}")
            
    async def send_limits(self, event):
        try:
            await self.send(text_data=json.dumps({
                'notification': 'Outliers by user ID',
                'user_id': event['user_id'],
                'user_ids': event['user_ids'],
                'guest_id': event['guest_id'],
                'guest_ids': event['guest_ids'],
                'criteria_id': event['criteria_id'],
                'lower': event['lower'],
                'upper': event['upper'],
            }))
            #print(f"Sent current outliers by user ID for criteria {event['criteria_id']}.")
        except Exception as e:
            print(f"Error in send_limits: {e}")