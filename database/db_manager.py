"""
Управление базой данных для истории генераций
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from utils.path_utils import get_db_path, ensure_data_dir


class DatabaseManager:
    """Менеджер базы данных для хранения истории генераций"""
    
    def __init__(self, db_path: str = None):
        """
        Инициализация менеджера БД
        
        Args:
            db_path: Путь к файлу базы данных (если None, используется путь через утилиту)
        """
        if db_path is None:
            # Используем утилиту для получения правильного пути
            self.db_path = get_db_path()
        else:
            self.db_path = Path(db_path)
        
        # Создаем папку data если её нет
        ensure_data_dir()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Инициализация структуры базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица для истории генераций
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,  -- 'generate', 'edit', 'combine'
                prompt TEXT NOT NULL,
                negative_prompt TEXT,
                model TEXT NOT NULL,
                resolution TEXT,
                image_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                parameters TEXT,  -- JSON с дополнительными параметрами
                credits_used REAL
            )
        """)
        
        # Таблица для пакетных генераций
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                image_path TEXT,
                status TEXT DEFAULT 'pending',  -- 'pending', 'completed', 'failed'
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES batches(id)
            )
        """)
        
        # Индексы для быстрого поиска
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_type ON generations(type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON generations(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_batch_id ON batch_generations(batch_id)
        """)
        
        conn.commit()
        conn.close()
    
    def add_generation(self, gen_type: str, prompt: str, model: str, 
                      image_path: str, resolution: str = None,
                      negative_prompt: str = None, parameters: dict = None,
                      credits_used: float = None) -> int:
        """
        Добавить запись о генерации
        
        Args:
            gen_type: Тип генерации ('generate', 'edit', 'combine')
            prompt: Текстовый промпт
            model: Использованная модель
            image_path: Путь к сохраненному изображению
            resolution: Разрешение изображения
            negative_prompt: Негативный промпт
            parameters: Дополнительные параметры
            credits_used: Использованные кредиты
            
        Returns:
            ID созданной записи
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        parameters_json = json.dumps(parameters) if parameters else None
        
        cursor.execute("""
            INSERT INTO generations 
            (type, prompt, negative_prompt, model, resolution, image_path, parameters, credits_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (gen_type, prompt, negative_prompt, model, resolution, 
              str(image_path), parameters_json, credits_used))
        
        gen_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return gen_id
    
    def get_generations(self, limit: int = 100, offset: int = 0,
                       gen_type: Optional[str] = None,
                       search_query: Optional[str] = None) -> List[Dict]:
        """
        Получить список генераций
        
        Args:
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            gen_type: Фильтр по типу генерации
            search_query: Поиск по промпту
            
        Returns:
            Список словарей с данными генераций
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM generations WHERE 1=1"
        params = []
        
        if gen_type:
            query += " AND type = ?"
            params.append(gen_type)
        
        if search_query:
            query += " AND prompt LIKE ?"
            params.append(f"%{search_query}%")
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            gen_dict = dict(row)
            # Парсим JSON параметры
            if gen_dict.get("parameters"):
                try:
                    gen_dict["parameters"] = json.loads(gen_dict["parameters"])
                except:
                    pass
            result.append(gen_dict)
        
        conn.close()
        return result
    
    def get_generation_by_id(self, gen_id: int) -> Optional[Dict]:
        """
        Получить генерацию по ID
        
        Args:
            gen_id: ID генерации
            
        Returns:
            Словарь с данными генерации или None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM generations WHERE id = ?", (gen_id,))
        row = cursor.fetchone()
        
        if row:
            result = dict(row)
            if result.get("parameters"):
                try:
                    result["parameters"] = json.loads(result["parameters"])
                except:
                    pass
            conn.close()
            return result
        
        conn.close()
        return None
    
    def delete_generation(self, gen_id: int) -> bool:
        """
        Удалить генерацию
        
        Args:
            gen_id: ID генерации
            
        Returns:
            True если успешно удалено
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM generations WHERE id = ?", (gen_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    def delete_generation_by_image_path(self, image_path: str) -> bool:
        """
        Удалить генерацию по пути к изображению
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            True если успешно удалено
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM generations WHERE image_path = ?", (image_path,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    def get_statistics(self) -> Dict:
        """
        Получить статистику по генерациям
        
        Returns:
            Словарь со статистикой
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Общее количество
        cursor.execute("SELECT COUNT(*) FROM generations")
        total = cursor.fetchone()[0]
        
        # По типам
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM generations 
            GROUP BY type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Общие кредиты
        cursor.execute("SELECT SUM(credits_used) FROM generations WHERE credits_used IS NOT NULL")
        total_credits = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total": total,
            "by_type": by_type,
            "total_credits": total_credits
        }

