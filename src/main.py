import time

from fastapi import (
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi_pagination import add_pagination
from starlette.responses import FileResponse

from src.auth.auth import (
    auth_backend,
    fastapi_users,
    google_oauth_client,
    vk_oauth_client,
)
from src.auth.router import auth_router, users_router
from src.auth.schemas import UserCreateSchema, UserReadSchema
from src.chat.router import chat_router
from src.sports.router import sports_router

from .schemas import HealthcheckResponse

app = FastAPI(
    title="Atlecta API",
    swagger_ui_parameters={"displayRequestDuration": True},
    docs_url=None, redoc_url=None
)
add_pagination(app)

origins = [
    "https://atlecta.ru",
    "https://api.atlecta.ru",
    "http://atlecta.ru",
    "http://api.atlecta.ru",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

favicon_url = "favicon-96x96.png"


@app.get("/healthcheck", response_model=HealthcheckResponse)
async def healthcheck():
    """
    Health check endpoint.

    Returns the current status of the API service. 
    Useful for monitoring and ensuring the server is running.

    Returns:
        dict: A simple dictionary with a "status" key indicating service health.
    """
    return HealthcheckResponse(status="healthy")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_url)


@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(openapi_url="/openapi.json", title=app.title + " - Swagger UI", swagger_favicon_url="favicon.ico", swagger_ui_parameters={"displayRequestDuration": True})


@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
    return get_redoc_html(openapi_url="/openapi.json", title=app.title + " - ReDoc", redoc_favicon_url="favicon.ico")


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserReadSchema, UserCreateSchema),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserReadSchema),
    prefix="/auth/verification",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_oauth_router(
        # WARNING: Change SECRET to something strong
        google_oauth_client, auth_backend, "SECRET",
        associate_by_email=True),
    prefix="/auth/google",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_oauth_router(
        # WARNING: Change SECRET to something strong
        vk_oauth_client, auth_backend, "SECRET", redirect_url="http://localhost/auth/vk/callback"),
    prefix="/auth/vk",
    tags=["auth"]
)
app.include_router(
    auth_router
)
app.include_router(
    users_router
)
app.include_router(
    sports_router
)
app.include_router(
    chat_router
)


@app.get('/list_endpoints')
def list_endpoints(request: Request):
    url_list = [
        route.path
        for route in request.app.routes
    ]
    return url_list

# Middleware


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Prints endpoint response time
    """
    start_time = time.time()
    response = await call_next(request)
    print("Time took to process the request and return response is {} sec".format(
        time.time() - start_time))
    return response


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://api.atlecta.ru/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
