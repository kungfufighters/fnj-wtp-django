from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from wheretoplayApp.models import Vote, VotingSession, Workspace, Opportunity

class VotingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.voting_session = '12345'
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
            session_id = data.get('session_id')
            user_id = data.get('user_id')

            print(f"Received vote data - Votes: {votes}, session_id: {session_id}, user_id: {user_id}")

            if votes and session_id and user_id:
                await self.insert_vote(session_id, user_id, votes[0]['vote_score'], votes[0]['criteria_id'])

                # Broadcast the vote to other users in the session
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
            else:
                print("Missing required fields in received data.")
        except json.JSONDecodeError:
            print("Error decoding JSON data")

    @database_sync_to_async
    def insert_vote(self, session_id, user_id, score, category):
        try:
            workspace = Workspace.objects.get(code=session_id)
            opportunity = Opportunity.objects.filter(workspace=workspace).first()

            if opportunity:
                Vote.objects.create(
                    opportunity=opportunity,
                    user_id=user_id,
                    vote_score=score,
                    criteria_id=category
                )
                print(f"Vote inserted for user {user_id} in session {session_id}")
            else:
                print(f"No opportunity found for workspace with code {session_id}")
        except Exception as e:
            print(f"Error inserting vote: {e}")

    async def broadcast_protocol(self, event):
        try:
            votes = await self.get_votes(event['criteria_id'], event['session_id'])
            await self.send(text_data=json.dumps({
                'result': votes,
                'criteria_id': event['criteria_id']
            }))
            print(f"Broadcasted votes for criteria {event['criteria_id']}")
        except Exception as e:
            print(f"Error in broadcast_protocol: {e}")

    @database_sync_to_async
    def get_votes(self, criteria_id, session_id):
        try:
            workspace = Workspace.objects.get(code=session_id)
            opportunity = Opportunity.objects.filter(workspace=workspace).first()
            votes = Vote.objects.filter(criteria_id=criteria_id, opportunity=opportunity)

            vote_counts = [0, 0, 0, 0, 0]
            for vote in votes:
                if 1 <= vote.vote_score <= 5:
                    vote_counts[vote.vote_score - 1] += 1
            print(f"Vote counts for criteria {criteria_id} in session {session_id}: {vote_counts}")
            return vote_counts
        except Workspace.DoesNotExist:
            print(f"Workspace with code {session_id} does not exist.")
            return [0, 0, 0, 0, 0]
        except Exception as e:
            print(f"Error retrieving votes: {e}")
            return [0, 0, 0, 0, 0]


    # @database_sync_to_async
    # def detect_outliers(self, votes, current_vote_score, threshold=2):
    #     """
    #     Use Median Absolute Deviation (MAD) to detect if a vote is an outlier.
    #     """
    #     votes_array = np.array(votes)
    #     median = np.median(votes_array)
    #     abs_deviation = np.abs(votes_array - median)
    #     mad = np.median(abs_deviation)
    #     lower_limit = median - (threshold * mad)
    #     upper_limit = median + (threshold * mad)

    #     is_outlier = not (lower_limit <= current_vote_score <= upper_limit)
    #     print(f"Vote {current_vote_score} is {'an outlier' if is_outlier else 'not an outlier'} for criteria.")
    #     return is_outlier
