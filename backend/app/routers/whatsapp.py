from fastapi import APIRouter
import sqlite3
from typing import List, Dict, Any

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

def get_conn():
    return sqlite3.connect('/root/ai-bot/data/whatsapp/whatsapp.db')

@router.get('/chats')
def list_chats() -> List[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT chat_name FROM whatsapp_messages ORDER BY chat_name')
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

@router.get('/{chat_name}')
def get_chat(chat_name: str, search: str = '', limit: int = 500, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    if search:
        search_term = f"%{search}%"
        cur.execute(
            '''SELECT timestamp, sender, message FROM whatsapp_messages 
               WHERE chat_name = ? AND (sender LIKE ? OR message LIKE ?)
               ORDER BY timestamp LIMIT ? OFFSET ?''',
            (chat_name, search_term, search_term, limit, offset)
        )
    else:
        cur.execute(
            'SELECT timestamp, sender, message FROM whatsapp_messages WHERE chat_name = ? ORDER BY timestamp LIMIT ? OFFSET ?',
            (chat_name, limit, offset)
        )
    rows = cur.fetchall()
    conn.close()
    return [{'timestamp': t, 'sender': s, 'message': m} for t, s, m in rows]

@router.delete('/{chat_name}/delete')
def delete_chat(chat_name: str) -> Dict[str, str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM whatsapp_messages WHERE chat_name = ?', (chat_name,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "chat_name": chat_name}
