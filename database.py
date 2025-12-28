
import sqlite3
import json
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер бази даних SQLite для системи адаптивного навчання"""
    
    def __init__(self, db_path: str = "adaptive_learning.db"):
        self.db_path = db_path
        self.connection = None
        self._init_db()
    
    def _get_connection(self):
        """Отримання з'єднання з базою даних"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def _init_db(self):
        """Ініціалізація структури бази даних"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Користувачі
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Байєсові моделі
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bayesian_models (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            network_structure TEXT NOT NULL,
            cpt_parameters TEXT NOT NULL,
            current_state TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # Завдання
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            task_type TEXT NOT NULL,
            condition TEXT NOT NULL,
            question TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            solution_steps TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Відповіді
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            user_response TEXT NOT NULL,
            is_correct BOOLEAN,
            time_spent INTEGER,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
        ''')
        
        # Індекси
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_user ON answers(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_task ON answers(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_topic ON tasks(topic)")
        
        conn.commit()
        logger.info("База даних ініціалізована")
    
    # ========== КОРИСТУВАЧІ ==========
    
    def create_user(self, username: str, email: str, role: str = "student") -> str:
        """Створення нового користувача"""
        user_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO users (id, username, email, role)
        VALUES (?, ?, ?, ?)
        ''', (user_id, username, email, role))
        
        conn.commit()
        return user_id
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Отримання користувача за email"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    # ========== БАЙЄСОВІ МОДЕЛІ ==========
    
    def create_bayesian_model(self, user_id: str, network_structure: Dict, 
                              cpt_parameters: Dict, current_state: Dict) -> str:
        """Створення Байєсової моделі"""
        model_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO bayesian_models (id, user_id, network_structure, cpt_parameters, current_state)
        VALUES (?, ?, ?, ?, ?)
        ''', (model_id, user_id, 
              json.dumps(network_structure, ensure_ascii=False),
              json.dumps(cpt_parameters, ensure_ascii=False),
              json.dumps(current_state, ensure_ascii=False)))
        
        conn.commit()
        return model_id
    
    def update_bayesian_model(self, user_id: str, current_state: Dict) -> bool:
        """Оновлення стану Байєсової моделі"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE bayesian_models 
        SET current_state = ?, created_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        ''', (json.dumps(current_state, ensure_ascii=False), user_id))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def get_bayesian_model(self, user_id: str) -> Optional[Dict]:
        """Отримання Байєсової моделі користувача"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bayesian_models WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            data = dict(row)
            # Конвертуємо JSON рядки назад у словники
            data['network_structure'] = json.loads(data['network_structure'])
            data['cpt_parameters'] = json.loads(data['cpt_parameters'])
            data['current_state'] = json.loads(data['current_state'])
            return data
        return None
    
    def delete_bayesian_model(self, user_id: str) -> bool:
        """Видалення моделі користувача"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM bayesian_models WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    # ========== ЗАВДАННЯ ==========
    
    def create_task(self, topic: str, difficulty: str, task_type: str, 
                    condition: str, question: str, correct_answer: str, 
                    solution_steps: List[str]) -> str:
        """Створення завдання"""
        task_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO tasks (id, topic, difficulty, task_type, condition, question, correct_answer, solution_steps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, topic, difficulty, task_type, condition, question, 
              correct_answer, json.dumps(solution_steps, ensure_ascii=False)))
        
        conn.commit()
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Отримання завдання за ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        if row:
            data = dict(row)
            data['solution_steps'] = json.loads(data['solution_steps'])
            return data
        return None
    
    def get_tasks_by_topic(self, topic: str, limit: int = 10) -> List[Dict]:
        """Отримання завдань за темою"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM tasks 
        WHERE topic = ? 
        ORDER BY RANDOM() 
        LIMIT ?
        ''', (topic, limit))
        
        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            task['solution_steps'] = json.loads(task['solution_steps'])
            tasks.append(task)
        
        return tasks
    
    # ========== ВІДПОВІДІ ==========
    
    def create_answer(self, user_id: str, task_id: str, user_response: str, 
                      is_correct: bool, time_spent: int = 0) -> str:
        """Запис відповіді учня"""
        answer_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO answers (id, user_id, task_id, user_response, is_correct, time_spent)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (answer_id, user_id, task_id, user_response, is_correct, time_spent))
        
        conn.commit()
        return answer_id
    
    def get_user_answers(self, user_id: str) -> List[Dict]:
        """Отримання всіх відповідей користувача"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT a.*, t.topic, t.difficulty
        FROM answers a
        JOIN tasks t ON a.task_id = t.id
        WHERE a.user_id = ?
        ORDER BY a.submitted_at DESC
        ''', (user_id,))
        
        answers = []
        for row in cursor.fetchall():
            answers.append(dict(row))
        
        return answers
    
    def get_user_statistics(self, user_id: str) -> Dict:
        """Статистика користувача"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Загальна статистика
        cursor.execute('''
        SELECT 
            COUNT(*) as total_answers,
            SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers,
            AVG(time_spent) as avg_time_spent
        FROM answers 
        WHERE user_id = ?
        ''', (user_id,))
        
        stats_row = cursor.fetchone()
        stats = dict(stats_row) if stats_row else {}
        
        # Статистика по темах
        cursor.execute('''
        SELECT 
            t.topic,
            COUNT(*) as total,
            SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) as correct
        FROM answers a
        JOIN tasks t ON a.task_id = t.id
        WHERE a.user_id = ?
        GROUP BY t.topic
        ''', (user_id,))
        
        stats['by_topic'] = []
        for row in cursor.fetchall():
            topic_stats = dict(row)
            if topic_stats['total'] > 0:
                topic_stats['accuracy'] = topic_stats['correct'] / topic_stats['total']
            else:
                topic_stats['accuracy'] = 0
            stats['by_topic'].append(topic_stats)
        
        return stats
    
    def close(self):
        """Закриття з'єднання"""
        if self.connection:
            self.connection.close()
            self.connection = None
