import json
import re
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Conversation, Message, Memory
from backend.schemas import (
    ConversationResponse,
    ConversationDetailResponse,
    ConversationCreate,
    MessageResponse,
    ChatRequest,
    ChatResponse
)
from backend.auth import get_current_user, get_optional_current_user
from backend.ai_service import ai_service
from backend.memory_service import memory_service
from backend.config import settings

router = APIRouter(prefix=settings.API_PREFIX, tags=["Chat & Conversations"])

# --- Conversations Management ---

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all conversations for the authenticated user."""
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    result = []
    for c in convs:
        count = db.query(Message).filter(Message.conversation_id == c.id).count()
        result.append(
            ConversationResponse(
                id=c.id,
                user_id=c.user_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=count
            )
        )
    return result

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    req: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    title = req.title.strip() if req.title and req.title.strip() else "New Conversation"
    conv = Conversation(user_id=current_user.id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0
    )

@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_details(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation details and full message history."""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return ConversationDetailResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(messages),
        messages=[MessageResponse.model_validate(m) for m in messages]
    )

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its messages."""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    db.delete(conv)
    db.commit()
    return {"message": "Conversation deleted successfully", "id": conversation_id}


# --- Chat Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Standard non-streaming AI chat endpoint."""
    user_id = current_user.id if current_user else None

    # Handle conversation
    conv = None
    if current_user:
        if req.conversation_id:
            conv = db.query(Conversation).filter(
                Conversation.id == req.conversation_id,
                Conversation.user_id == current_user.id
            ).first()

        if not conv:
            # Generate title from first 30 chars of message
            title = req.message.strip()[:35] + ("..." if len(req.message.strip()) > 35 else "")
            conv = Conversation(user_id=current_user.id, title=title)
            db.add(conv)
            db.commit()
            db.refresh(conv)

        # Store user message
        user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
        db.add(user_msg)
        conv.updated_at = datetime.utcnow()

        # Auto-detect explicit user details like name or studies or location and store in memory vault
        msg_lower = req.message.lower()
        if "my name is " in msg_lower or "call me " in msg_lower:
            name_m = re.search(r"(?:my name is|call me)\s+([A-Za-z]+)", req.message, re.IGNORECASE)
            if name_m:
                detected = name_m.group(1).capitalize()
                if detected.lower() not in ("dakshu", "not", "feeling", "fine", "good"):
                    has_mem = db.query(Memory).filter(Memory.user_id == current_user.id, Memory.memory_text.contains(detected)).first()
                    if not has_mem:
                        memory_service.add_memory(db, current_user.id, f"User's name is {detected}")

        if any(term in msg_lower for term in ["i live in", "i am from", "my location is", "my city is"]):
            loc_m = re.search(r"(?:i live in|i am from|my location is|my city is)\s+([A-Za-z\s,]+)", req.message, re.IGNORECASE)
            if loc_m:
                detected_loc = loc_m.group(1).strip()
                if 2 < len(detected_loc) < 50:
                    has_loc = db.query(Memory).filter(Memory.user_id == current_user.id, Memory.memory_text.contains(detected_loc)).first()
                    if not has_loc:
                        memory_service.add_memory(db, current_user.id, f"User's location is {detected_loc}")

        # Store live detected GPS/browser location if passed
        if req.client_location:
            has_live_loc = db.query(Memory).filter(Memory.user_id == current_user.id, Memory.memory_text.contains("Live detected location")).first()
            if not has_live_loc:
                memory_service.add_memory(db, current_user.id, f"Live detected location is {req.client_location}")
            else:
                has_live_loc.memory_text = f"Live detected location is {req.client_location}"

        db.commit()

    # Load context history
    history_messages = []
    if conv:
        past_msgs = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(settings.MAX_HISTORY_TURNS * 2)
            .all()
        )
        for m in reversed(past_msgs):
            history_messages.append({"role": m.role, "content": m.content})
    else:
        history_messages.append({"role": "user", "content": req.message})

    # Prepare memory context injection with timezone and location
    memory_injection = memory_service.build_context_injection(
        db, user_id, req.message,
        client_timezone=req.client_timezone,
        client_location=req.client_location
    )

    # Generate response
    assistant_content = await ai_service.generate_response(
        messages=history_messages,
        module=req.module or "companion",
        memory_injection=memory_injection
    )

    msg_id = 0
    conv_id = conv.id if conv else 0

    if conv:
        asst_msg = Message(conversation_id=conv.id, role="assistant", content=assistant_content)
        db.add(asst_msg)
        conv.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(asst_msg)
        msg_id = asst_msg.id

    return ChatResponse(
        conversation_id=conv_id,
        message_id=msg_id,
        role="assistant",
        content=assistant_content,
        module=req.module or "companion",
        created_at=datetime.utcnow()
    )


@router.post("/chat/stream")
async def chat_stream_endpoint(
    req: ChatRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Streaming Server-Sent Events (SSE) AI chat endpoint."""
    user_id = current_user.id if current_user else None

    conv = None
    if current_user:
        if req.conversation_id:
            conv = db.query(Conversation).filter(
                Conversation.id == req.conversation_id,
                Conversation.user_id == current_user.id
            ).first()

        if not conv:
            title = req.message.strip()[:35] + ("..." if len(req.message.strip()) > 35 else "")
            conv = Conversation(user_id=current_user.id, title=title)
            db.add(conv)
            db.commit()
            db.refresh(conv)

        user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
        db.add(user_msg)
        conv.updated_at = datetime.utcnow()

        msg_lower = req.message.lower()
        if "my name is " in msg_lower or "call me " in msg_lower:
            name_m = re.search(r"(?:my name is|call me)\s+([A-Za-z]+)", req.message, re.IGNORECASE)
            if name_m:
                detected = name_m.group(1).capitalize()
                if detected.lower() not in ("dakshu", "not", "feeling", "fine", "good"):
                    has_mem = db.query(Memory).filter(Memory.user_id == current_user.id, Memory.memory_text.contains(detected)).first()
                    if not has_mem:
                        memory_service.add_memory(db, current_user.id, f"User's name is {detected}")

        db.commit()

    history_messages = []
    if conv:
        past_msgs = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(settings.MAX_HISTORY_TURNS * 2)
            .all()
        )
        for m in reversed(past_msgs):
            history_messages.append({"role": m.role, "content": m.content})
    else:
        history_messages.append({"role": "user", "content": req.message})

    memory_injection = memory_service.build_context_injection(
        db, user_id, req.message,
        client_timezone=req.client_timezone,
        client_location=req.client_location
    )
    conv_id = conv.id if conv else 0

    async def event_generator():
        accumulated_chunks = []
        try:
            async for chunk in ai_service.stream_response(
                messages=history_messages,
                module=req.module or "companion",
                memory_injection=memory_injection
            ):
                accumulated_chunks.append(chunk)
                payload = json.dumps({"chunk": chunk, "conversation_id": conv_id, "done": False})
                yield f"data: {payload}\n\n"

            # Generation completed
            full_content = "".join(accumulated_chunks)
            asst_msg_id = 0

            # Save assistant message to DB
            if conv:
                asst_msg = Message(conversation_id=conv.id, role="assistant", content=full_content)
                db.add(asst_msg)
                conv.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(asst_msg)
                asst_msg_id = asst_msg.id

            done_payload = json.dumps({
                "done": True,
                "message_id": asst_msg_id,
                "conversation_id": conv_id,
                "module": req.module or "companion"
            })
            yield f"data: {done_payload}\n\n"
        except Exception as e:
            err_payload = json.dumps({"error": str(e), "done": True})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

