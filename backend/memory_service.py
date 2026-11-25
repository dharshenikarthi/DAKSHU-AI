from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models import Memory, UserPreference, User
from backend.schemas import UserPreferenceUpdate

class MemoryService:
    @staticmethod
    def get_user_preferences(db: Session, user_id: int) -> UserPreference:
        prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not prefs:
            prefs = UserPreference(
                user_id=user_id,
                preferred_language="tanglish",
                response_style="friendly",
                voice_enabled=True
            )
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return prefs

    @staticmethod
    def update_user_preferences(db: Session, user_id: int, update_data: UserPreferenceUpdate) -> UserPreference:
        prefs = MemoryService.get_user_preferences(db, user_id)
        if update_data.preferred_language is not None:
            prefs.preferred_language = update_data.preferred_language
        if update_data.response_style is not None:
            prefs.response_style = update_data.response_style
        if update_data.voice_enabled is not None:
            prefs.voice_enabled = update_data.voice_enabled
        db.commit()
        db.refresh(prefs)
        return prefs

    @staticmethod
    def get_memories(db: Session, user_id: int) -> List[Memory]:
        return db.query(Memory).filter(Memory.user_id == user_id).order_by(Memory.created_at.desc()).all()

    @staticmethod
    def add_memory(db: Session, user_id: int, memory_text: str) -> Memory:
        # Sanitize and truncate
        cleaned_text = memory_text.strip()[:1000]
        memory = Memory(user_id=user_id, memory_text=cleaned_text)
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    @staticmethod
    def delete_memory(db: Session, user_id: int, memory_id: int) -> bool:
        memory = db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == user_id).first()
        if not memory:
            return False
        db.delete(memory)
        db.commit()
        return True

    @staticmethod
    def build_context_injection(
        db: Session,
        user_id: Optional[int],
        current_query: str,
        client_timezone: Optional[str] = None,
        client_location: Optional[str] = None
    ) -> str:
        """
        Builds dynamic context injection for Dakshu's prompt based on real-time clock,
        timezone, location, user preferences, and relevant memories. Separate from chat history.
        """
        from backend.config import get_localized_now
        tz_str = client_timezone or "Asia/Kolkata"
        now = get_localized_now(tz_str)
        context_lines = []
        context_lines.append("\n=== REAL-TIME CONTEXT & USER MEMORY ===")
        context_lines.append(f"- Current Day & Date: {now.strftime('%A, %B %d, %Y')}")
        context_lines.append(f"- Current Local Time: {now.strftime('%I:%M %p')}")
        context_lines.append(f"- User Timezone: {tz_str}")
        if client_location:
            context_lines.append(f"- User Detected/Saved Location: {client_location}")

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.full_name:
                first_name = user.full_name.split()[0].capitalize()
                context_lines.append(f"- User Full Name: {user.full_name} (Call them {first_name})")

            prefs = MemoryService.get_user_preferences(db, user_id)
            memories = MemoryService.get_memories(db, user_id)

            context_lines.append(f"- Preferred Language: {prefs.preferred_language}")
            context_lines.append(f"- Preferred Communication Style: {prefs.response_style}")

            if memories:
                context_lines.append("- Explicitly Saved User Context:")
                # Inject memories (most recent first, up to 10 memories)
                for mem in memories[:10]:
                    context_lines.append(f"  * {mem.memory_text}")
            else:
                context_lines.append("- No explicit memories saved yet.")

        context_lines.append("Instructions: Respect these preferences warmly and naturally. Never invent remembered facts.")
        context_lines.append("=====================================\n")

        return "\n".join(context_lines)

memory_service = MemoryService()

