import sqlite3
import json
import os
from datetime import datetime

class DebrisLedger:
    def __init__(self, db_path="mission_debris_ledger.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create Elements Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS elements (
                id TEXT PRIMARY KEY,
                mission_id TEXT,
                category TEXT, 
                mass_kg REAL,
                status TEXT,
                disposal_strategy TEXT,
                metrics JSON,
                last_updated TEXT
            )
        ''')
        
        # Create Reports/Audit Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT,
                report_type TEXT,
                content JSON,
                timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_element(self, element_id, mission_id, category, mass_kg, strategy, metrics=None):
        if metrics is None:
            metrics = {}
            
        status = "PRE-LAUNCH"
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO elements (id, mission_id, category, mass_kg, status, disposal_strategy, metrics, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (element_id, mission_id, category, mass_kg, status, strategy, json.dumps(metrics), now))
        conn.commit()
        conn.close()

    def update_element_status(self, element_id, new_status):
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE elements SET status = ?, last_updated = ? WHERE id = ?
        ''', (new_status, now, element_id))
        conn.commit()
        conn.close()

    def fetch_mission_elements(self, mission_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM elements WHERE mission_id = ?', (mission_id,))
        rows = cursor.fetchall()
        conn.close()
        
        elements = []
        for row in rows:
            elements.append({
                "id": row[0],
                "mission_id": row[1],
                "category": row[2],
                "mass_kg": row[3],
                "status": row[4],
                "disposal_strategy": row[5],
                "metrics": json.loads(row[6]),
                "last_updated": row[7]
            })
        return elements

    def save_compliance_report(self, mission_id, report_type, content):
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO compliance_reports (mission_id, report_type, content, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (mission_id, report_type, json.dumps(content), now))
        conn.commit()
        conn.close()
