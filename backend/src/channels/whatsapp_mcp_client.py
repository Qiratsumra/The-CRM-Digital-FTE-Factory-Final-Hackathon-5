"""WhatsApp MCP Client - Direct SQLite Database Access"""
import aiosqlite
import httpx
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppMessage:
    id: str
    chat_jid: str
    from_jid: str
    message_text: str
    timestamp: datetime
    is_from_me: bool
    is_read: bool


class WhatsAppDatabaseClient:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._db = None

    async def connect(self) -> bool:
        try:
            if not self.db_path.exists():
                logger.error(f"WhatsApp database not found at: {self.db_path}")
                return False
            self._db = await aiosqlite.connect(str(self.db_path))
            self._db.row_factory = aiosqlite.Row
            logger.info(f"Connected to WhatsApp database: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WhatsApp database: {e}")
            return False

    async def close(self):
        if self._db:
            await self._db.close()

    async def get_unread_messages(self, chat_jid=None) -> list:
        if not self._db:
            return []
        try:
            async with self._db.execute(
                """SELECT id, chat_jid, sender, content, timestamp, is_from_me
                FROM messages
                WHERE is_from_me = 0
                AND (chat_jid = ? OR ? IS NULL)
                ORDER BY timestamp ASC""",
                (chat_jid, chat_jid)
            ) as cursor:
                rows = await cursor.fetchall()
                messages = []
                for row in rows:
                    try:
                        ts = row[4]
                        if hasattr(ts, "timestamp"):
                            dt = ts
                        else:
                            dt = datetime.fromtimestamp(float(ts))
                    except Exception:
                        dt = datetime.now()
                    messages.append(WhatsAppMessage(
                        id=str(row[0]),
                        chat_jid=row[1],
                        from_jid=row[2] if row[2] else "",
                        message_text=row[3] or "",
                        timestamp=dt,
                        is_from_me=bool(row[5]),
                        is_read=False
                    ))
                return messages
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []

    async def get_all_chats(self) -> list:
        if not self._db:
            return []
        try:
            async with self._db.execute(
                "SELECT jid, name, last_message_time FROM chats ORDER BY last_message_time DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [{"jid": r[0], "name": r[1]} for r in rows]
        except Exception as e:
            logger.error(f"Failed to get chats: {e}")
            return []

    async def mark_message_read(self, message_id: str) -> bool:
        return True

    async def store_outgoing_message(self, chat_jid, from_jid, message_text) -> bool:
        return True


class WhatsAppMCPClient:
    def __init__(self, bridge_path: str, messages_db_path=None):
        self.bridge_path = Path(bridge_path)
        self.messages_db_path = (
            Path(messages_db_path) if messages_db_path
            else self.bridge_path / "store" / "messages.db"
        )
        self._db_client: Optional[WhatsAppDatabaseClient] = None
        self._initialized = False

    async def initialize(self) -> bool:
        try:
            self._db_client = WhatsAppDatabaseClient(self.messages_db_path)
            success = await self._db_client.connect()
            self._initialized = success
            return success
        except Exception as e:
            logger.error(f"WhatsApp MCP client initialization failed: {e}")
            return False

    async def close(self):
        if self._db_client:
            await self._db_client.close()
        self._initialized = False
        logger.info("WhatsApp MCP client closed")

    async def receive_message(self, phone_number: str) -> Optional[WhatsAppMessage]:
        if not self._initialized or not self._db_client:
            return None
        chat_jid = self._phone_to_jid(phone_number)
        messages = await self._db_client.get_unread_messages(chat_jid)
        return messages[0] if messages else None

    async def send_message(self, to_phone: str, message: str) -> bool:
        try:
            normalized_phone = self._normalize_phone_number(to_phone)
            logger.info(f"Normalized phone {to_phone} -> {normalized_phone}")
            logger.info(f"Attempting to send WhatsApp message to {to_phone} via REST API")

            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.post(
                        "http://localhost:8080/api/send",
                        json={"recipient": normalized_phone, "message": message},
                    )
                    logger.info(f"Bridge API response: {response.status_code} - {response.text}")
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            logger.info(f"WhatsApp message sent to {to_phone}")
                            return True
                        else:
                            logger.error(f"Bridge returned success=false: {result.get('message')}")
                            return False
                    return False
                except httpx.ReadTimeout:
                    logger.warning("Read timeout sending WhatsApp message")
                    return False

        except httpx.ConnectError as e:
            logger.error(f"Could not connect to WhatsApp bridge at localhost:8080: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}", exc_info=True)
            return False

    def _phone_to_jid(self, phone: str) -> str:
        cleaned = "".join(c for c in phone if c.isdigit())
        return f"{cleaned}@s.whatsapp.net"

    def _normalize_phone_number(self, phone: str) -> str:
        cleaned = "".join(c for c in phone if c.isdigit())
        # 03XXXXXXXXX (11 digits) -> 923XXXXXXXXX
        if cleaned.startswith("0") and len(cleaned) == 11:
            cleaned = "92" + cleaned[1:]
        # 3XXXXXXXXX (10 digits) -> 923XXXXXXXXX
        if len(cleaned) == 10 and cleaned.startswith("3"):
            cleaned = "92" + cleaned
        return cleaned

    async def check_go_bridge_status(self) -> bool:
        bridge_exe = self.bridge_path / "whatsapp-bridge.exe"
        if not bridge_exe.exists():
            bridge_exe = self.bridge_path / "whatsapp-bridge"
        return bridge_exe.exists()


async def send_whatsapp_message(phone: str, message: str, client=None) -> bool:
    if client is None:
        client = WhatsAppMCPClient(bridge_path="./whatsapp-mcp/whatsapp-bridge")
        await client.initialize()
        try:
            return await client.send_message(phone, message)
        finally:
            await client.close()
    return await client.send_message(phone, message)


async def receive_whatsapp_message(phone: str, client=None) -> Optional[WhatsAppMessage]:
    if client is None:
        client = WhatsAppMCPClient(bridge_path="./whatsapp-mcp/whatsapp-bridge")
        await client.initialize()
        try:
            return await client.receive_message(phone)
        finally:
            await client.close()
    return await client.receive_message(phone)