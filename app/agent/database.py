import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class ConversationDB:
    """SQLite database for conversation history, incidents, and metrics."""

    def __init__(self, db_path: Path | str = "conversations.db"):
        self.db_path = Path(db_path)
        self.init_schema()

    def init_schema(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        c = conn.cursor()
        # Conversations table
        c.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                user_message TEXT,
                agent_response TEXT,
                intent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Incidents table (high-priority events like phishing)
        c.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                intent TEXT,
                severity TEXT,
                details TEXT,
                status TEXT DEFAULT 'open',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Metrics table (awareness tracking)
        c.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                value INTEGER,
                intent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_conversation(self, user_id: str, user_msg: str, agent_response: str, intent: str):
        """Save a conversation turn."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO conversations (user_id, user_message, agent_response, intent)
            VALUES (?, ?, ?, ?)
        """, (user_id, user_msg, agent_response, intent))
        conn.commit()
        conn.close()

    def save_incident(self, user_id: str, intent: str, severity: str, details: str):
        """Log a security incident (phishing, compromise, etc.)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO incidents (user_id, intent, severity, details)
            VALUES (?, ?, ?, ?)
        """, (user_id, intent, severity, details))
        conn.commit()
        conn.close()

    def increment_metric(self, metric_name: str, intent: str = ""):
        """Increment a metric counter (e.g., phishing_questions_asked)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO metrics (metric_name, value, intent)
            VALUES (?, 1, ?)
        """, (metric_name, intent))
        conn.commit()
        conn.close()

    def get_metrics_summary(self) -> Dict:
        """Return aggregated metrics for dashboard."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT metric_name, intent, COUNT(*) as count 
            FROM metrics 
            GROUP BY metric_name, intent
        """)
        rows = c.fetchall()
        conn.close()
        result = {}
        for metric_name, intent, count in rows:
            key = f"{metric_name}_{intent}" if intent else metric_name
            result[key] = count
        return result

    def get_open_incidents(self) -> List[Dict]:
        """Return all open incidents."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT id, user_id, intent, severity, details, timestamp 
            FROM incidents 
            WHERE status = 'open'
            ORDER BY timestamp DESC
        """)
        rows = c.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "user_id": row[1],
                "intent": row[2],
                "severity": row[3],
                "details": row[4],
                "timestamp": row[5]
            })
        return result

    def close_incident(self, incident_id: int):
        """Mark an incident as resolved."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE incidents SET status = 'closed' WHERE id = ?", (incident_id,))
        conn.commit()
        conn.close()

    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Retrieve conversation history for a user."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT user_message, agent_response, intent, timestamp 
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (user_id, limit))
        rows = c.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "user_message": row[0],
                "agent_response": row[1],
                "intent": row[2],
                "timestamp": row[3]
            })
        return result
