import uuid
from .services import ChatService, GroupService, MessageService, AttachmentService
from src.auth.schemas import UserReadSchema as UserSchema
from src.auth.auth import current_active_user as get_current_user
from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from typing import Any, List

from fastapi import WebSocket
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

# Assume these are in a dependencies module
from src.database import async_session_factory as get_db
from src.chat.schemas import (
    AttachmentSchema,
    ChatMemberResponseSchema,
    ChatSchema,
    GroupCreateSchema,
    GroupResponseSchema,
    MessageCreateSchema,
    MessageResponseSchema,
)

chat_router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)


@chat_router.post("/chats")
async def create_chat(chat_data: ChatSchema, current_user: UserSchema = Depends(get_current_user)) -> ChatSchema:
    chat = await ChatService().create(chat_data, current_user.id)
    return chat


@chat_router.post("/groups", response_model=GroupResponseSchema)
async def create_group_endpoint(group: GroupCreateSchema, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await create_group(group.name, user.id, db)


@chat_router.post("/groups/{group_id}/join", response_model=ChatMemberResponseSchema)
async def join_group_endpoint(group_id: UUID4, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await join_group(group_id, user.id, db)


@chat_router.post("/chats/{chat_id}/messages", response_model=MessageResponseSchema)
async def send_chat_message(chat_id: UUID4, message: MessageCreateSchema, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    message.chat_id = chat_id
    return await send_message(
        chat_id=message.chat_id,
        group_id=message.group_id,
        user_id=user.id,
        username=user.username,
        content=message.content,
        attachment_id=message.attachment_id,
        sport_object_id=message.sport_object_id,
        db=db
    )


@chat_router.post("/groups/{group_id}/messages", response_model=MessageResponseSchema)
async def send_group_message(group_id: UUID4, message: MessageCreateSchema, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    message.group_id = group_id
    return await send_message(
        chat_id=message.chat_id,
        group_id=message.group_id,
        user_id=user.id,
        username=user.username,
        content=message.content,
        attachment_id=message.attachment_id,
        sport_object_id=message.sport_object_id,
        db=db
    )


@chat_router.get("/groups/{group_id}/messages", response_model=list[MessageResponseSchema])
async def get_group_messages_endpoint(group_id: UUID4, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Verify user is in group
    member = await db.execute(select(ChatMember).filter_by(group_id=group_id, user_id=user.id))
    if not member.scalar():
        raise HTTPException(status_code=403, detail="User not in group")
    return await get_group_messages(group_id, db)


@chat_router.websocket("/ws/chats/{chat_id}")
async def websocket_chat(chat_id: UUID4, websocket: WebSocket, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Verify user is in chat
    member = await db.execute(select(ChatMember).filter_by(chat_id=chat_id, user_id=user.id))
    if not member.scalar():
        await websocket.close(code=1008)
        return
    await websocket.accept()
    if chat_id not in chat_connections:
        chat_connections[chat_id] = set()
    chat_connections[chat_id].add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = MessageCreateSchema(**data)
            await send_message(
                chat_id=chat_id,
                group_id=None,
                user_id=user.id,
                username=user.username,
                content=message.content,
                attachment_id=message.attachment_id,
                sport_object_id=message.sport_object_id,
                db=db
            )
    except Exception:
        chat_connections[chat_id].remove(websocket)
        if not chat_connections[chat_id]:
            del chat_connections[chat_id]
        await websocket.close()


@chat_router.websocket("/ws/groups/{group_id}")
async def websocket_group(group_id: UUID4, websocket: WebSocket, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Verify user is in group
    member = await db.execute(select(ChatMember).filter_by(group_id=group_id, user_id=user.id))
    if not member.scalar():
        await websocket.close(code=1008)
        return
    await websocket.accept()
    if group_id not in group_connections:
        group_connections[group_id] = set()
    group_connections[group_id].add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = MessageCreateSchema(**data)
            await send_message(
                chat_id=None,
                group_id=group_id,
                user_id=user.id,
                username=user.username,
                content=message.content,
                attachment_id=message.attachment_id,
                sport_object_id=message.sport_object_id,
                db=db
            )
    except Exception:
        group_connections[group_id].remove(websocket)
        if not group_connections[group_id]:
            del group_connections[group_id]
        await websocket.close()


@chat_router.post("/groups")
async def create_group(group_data: GroupCreateSchema, current_user: UserSchema = Depends(get_current_user)) -> GroupResponseSchema:
    group = await GroupService().create(group_data, current_user.id)
    return group


@chat_router.post("/groups/{group_id}/join")
async def join_group(group_id: int, current_user: UserSchema = Depends(get_current_user)) -> GroupResponseSchema:
    group = await GroupService().join(group_id, current_user.id)
    return group


@chat_router.post("/attachments")
async def upload_attachment(file: UploadFile = File(...)) -> AttachmentSchema:
    attachment = await AttachmentService().upload(file)
    return attachment


# @chat_router.post("/chats/{chat_id}/messages")
# async def send_chat_message(chat_id: int, message: MessageCreateSchema, current_user: UserSchema = Depends(get_current_user)) -> MessageResponseSchema:
#     message = await MessageService().send_chat_message(chat_id, message, current_user.id)
#     return message
#
#
# @chat_router.post("/groups/{group_id}/messages")
# async def send_group_message(group_id: int, message: MessageCreateSchema, current_user: UserSchema = Depends(get_current_user)) -> MessageResponseSchema:
#     message = await MessageService().send_group_message(group_id, message, current_user.id)
#     return message


@chat_router.get("/groups/{group_id}/messages")
async def get_group_messages(group_id: int, current_user: UserSchema = Depends(get_current_user)) -> List[MessageResponseSchema]:
    messages = await MessageService().get_group_messages(group_id, current_user.id)
    return messages

# Новые эндпоинты


@chat_router.get("/chats")
async def get_user_chats(current_user: UserSchema = Depends(get_current_user)) -> Any:
    # """
    # Retrieve a list of all chats (personal and group) for the current user.
    #
    # Returns:
    #     List[ChatSchema]: A list of all chats the user is part of.
    # """
    # chats = await ChatService().get_user_chats(current_user.id)
    # return chats
    """
    Retrieve a list of all chats for the current user with participant names.

    Returns:
        List[ChatWithParticipantsSchema]: A list of chats with participant details.
    """
    # Временная заглушка, пока функционал не готов
    return [
        {
            "chat_id": 1,
            "participants": [
                {"user_id": 2, "first_name": "Алексей", "last_name": "Иванов"}
            ]
        },
        {
            "chat_id": 2,
            "participants": [
                {"user_id": 3, "first_name": "Мария", "last_name": "Петрова"}
            ]
        },
        {
            "chat_id": 3,
            "participants": [
                {"user_id": 4, "first_name": "Дмитрий", "last_name": "Смирнов"},
                {"user_id": 5, "first_name": "Екатерина", "last_name": "Соколова"}
            ]
        }
    ]


@chat_router.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: uuid.UUID, current_user: UserSchema = Depends(get_current_user)) -> Any:
    # """
    # Retrieve all messages in a specific personal chat.
    #
    # Args:
    #     chat_id (int): The ID of the chat to retrieve messages from.
    #
    # Returns:
    #     List[MessageResponseSchema]: A list of messages in the specified chat.
    # """
    # messages = await MessageService().get_chat_messages(chat_id, current_user.id)
    # return messages
    return [
        {
            "message_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "chat_id": chat_id,
            "sender_id": "7d793037-a076-4a1d-8c3c-1e1a8e2f3b5d",
            "sender_first_name": "Алексей",
            "sender_last_name": "Иванов",
            "content": "Привет, как дела?",
            "timestamp": "2025-06-05T13:00:00Z",
            "attachment_id": "c9bf9e57-168d-4a36-8c74-1f3e9d2e8b1a"
        },
        {
            "message_id": "a87ff679-a2f3-4e5a-b2d2-5c5e7f8b9c0d",
            "chat_id": chat_id,
            "sender_id": "e4b2a8f0-5c2d-4a3e-9b1c-3f7d6e8c9a0b",
            "sender_first_name": "Biba",
            "sender_last_name": "Bobovich",
            "content": "Привет! Отлично, а у тебя?",
            "timestamp": "2025-06-05T13:01:00Z"
        }
    ]


@chat_router.get("/chats/{chat_id}")
async def get_chat_info(chat_id: int, current_user: UserSchema = Depends(get_current_user)) -> ChatSchema:
    """
    Retrieve information about a specific personal chat.

    Args:
        chat_id (int): The ID of the chat to retrieve.

    Returns:
        ChatSchema: The chat details, including participants and metadata.
    """
    chat = await ChatService().get_by_id(chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


@chat_router.get("/groups/{group_id}")
async def get_group_info(group_id: int, current_user: UserSchema = Depends(get_current_user)) -> GroupResponseSchema:
    """
    Retrieve information about a specific group chat.

    Args:
        group_id (int): The ID of the group to retrieve.

    Returns:
        GroupSchema: The group details, including participants and metadata.
    """
    group = await GroupService().get_by_id(group_id, current_user.id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


@chat_router.post("/groups/{group_id}/leave")
async def leave_group(group_id: int, current_user: UserSchema = Depends(get_current_user)) -> dict:
    """
    Leave a specific group chat.

    Args:
        group_id (int): The ID of the group to leave.

    Returns:
        dict: A confirmation message.
    """
    await GroupService().leave(group_id, current_user.id)
    return {"message": f"User {current_user.id} left group {group_id}"}


@chat_router.delete("/chats/{chat_id}/messages/{message_id}")
async def delete_chat_message(chat_id: int, message_id: int, current_user: UserSchema = Depends(get_current_user)) -> dict:
    """
    Delete a message from a personal chat.

    Args:
        chat_id (int): The ID of the chat containing the message.
        message_id (int): The ID of the message to delete.

    Returns:
        dict: A confirmation message.
    """
    await MessageService().delete_chat_message(chat_id, message_id, current_user.id)
    return {"message": f"Message {message_id} deleted from chat {chat_id}"}


@chat_router.delete("/groups/{group_id}/messages/{message_id}")
async def delete_group_message(group_id: int, message_id: int, current_user: UserSchema = Depends(get_current_user)) -> dict:
    """
    Delete a message from a group chat.

    Args:
        group_id (int): The ID of the group containing the message.
        message_id (int): The ID of the message to delete.

    Returns:
        dict: A confirmation message.
    """
    await MessageService().delete_group_message(group_id, message_id, current_user.id)
    return {"message": f"Message {message_id} deleted from group {group_id}"}


@chat_router.patch("/groups/{group_id}")
async def update_group(group_id: int, group_update: GroupCreateSchema, current_user: UserSchema = Depends(get_current_user)) -> GroupResponseSchema:
    """
    Update a group chat's details (e.g., name, description).

    Args:
        group_id (int): The ID of the group to update.
        group_update (GroupUpdateSchema): The updated group data.

    Returns:
        GroupSchema: The updated group details.
    """
    updated_group = await GroupService().update(group_id, group_update, current_user.id)
    return updated_group


@chat_router.post("/groups/{group_id}/add-user")
async def add_user_to_group(group_id: int, user_id: int, current_user: UserSchema = Depends(get_current_user)) -> GroupResponseSchema:
    """
    Add a user to a group chat.

    Args:
        group_id (int): The ID of the group to add the user to.
        user_id (int): The ID of the user to add.

    Returns:
        GroupSchema: The updated group details.
    """
    updated_group = await GroupService().add_user(group_id, user_id, current_user.id)
    return updated_group


@chat_router.post("/groups/{group_id}/remove-user")
async def remove_user_from_group(group_id: int, user_id: int, current_user: UserSchema = Depends(get_current_user)) -> GroupResponseSchema:
    """
    Remove a user from a group chat.

    Args:
        group_id (int): The ID of the group to remove the user from.
        user_id (int): The ID of the user to remove.

    Returns:
        GroupSchema: The updated group details.
    """
    updated_group = await GroupService().remove_user(group_id, user_id, current_user.id)
    return updated_group


@chat_router.post("/attachments", response_model=AttachmentSchema)
async def upload_attachment_endpoint(file: UploadFile = File(...), user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=400, detail="Only JPEG or PNG images allowed")
    content = await file.read()
    return await create_attachment(content, "image", db)


@chat_router.get("/attachments/{attachment_id}")
async def get_attachment(attachment_id: int) -> FileResponse:
    """
    Retrieve a specific attachment by its ID.

    Args:
        attachment_id (int): The ID of the attachment to retrieve.

    Returns:
        FileResponse: The attachment file for download.
    """
    attachment = await AttachmentService().get_by_id(attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return FileResponse(attachment.file_path, media_type=attachment.content_type, filename=attachment.filename)
