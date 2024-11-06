# wheretoplay/routing.py
from django.urls import re_path
from wheretoplayApp.consumers import VotingConsumer  # Import the WebSocket consumer

# Define WebSocket URL patterns
websocket_urlpatterns = [
    re_path(r'ws/vote/(?P<code>\d{5})/$', VotingConsumer.as_asgi()),
    #re_path(r'ws/test/$', SurveyConsumer.as_asgi()),  # WebSocket route for /ws/test/
]
