import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import wheretoplay.routing  # Import your routing file

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wheretoplay.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handle HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(
            wheretoplay.routing.websocket_urlpatterns  # WebSocket routing patterns
        )
    ),
})
