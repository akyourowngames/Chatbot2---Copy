"""
💾 STORAGE ENGINE — The Data Vault 🗄️
Advanced data storage system for scraped content with multiple format support.
"""

import json
import csv
import sqlite3
import logging
import os
import pickle
import pandas as pd
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
from pathlib import Path
import gzip
import shutil
from contextlib import contextmanager
import threading
from concurrent.futures import ThreadPoolExecutor

@dataclass
class StorageConfig:
    """Configuration for storage operations"""
    base_path: str = "scraped_data"
    format: str = "json"  # json, csv, sqlite, pickle, parquet
    compress: bool = False
    backup: bool = True
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    batch_size: int = 1000
    auto_cleanup: bool = True
    cleanup_days: int = 30
    indexing: bool = True
    encryption: bool = False
    encryption_key: str = None

class DataStorage:
    """
    💾 Advanced data storage system with multiple format support
    """
    
    def __init__(self, config: StorageConfig = None):
        self.config = config or StorageConfig()
        self.base_path = Path(self.config.base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.json_path = self.base_path / "json"
        self.csv_path = self.base_path / "csv"
        self.db_path = self.base_path / "database"
        self.backup_path = self.base_path / "backups"
        
        for path in [self.json_path, self.csv_path, self.db_path, self.backup_path]:
            path.mkdir(exist_ok=True)
        
        # Thread lock for concurrent access
        self.lock = threading.Lock()
        
        # Initialize database if using SQLite
        if self.config.format == "sqlite":
            self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with proper schema"""
        try:
            db_file = self.db_path / "scraped_data.db"
            
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                
                # Create main content table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scraped_content (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT UNIQUE NOT NULL,
                        title TEXT,
                        content TEXT,
                        summary TEXT,
                        author TEXT,
                        publish_date TEXT,
                        tags TEXT,
                        entities TEXT,
                        sentiment TEXT,
                        language TEXT,
                        word_count INTEGER,
                        reading_time INTEGER,
                        images TEXT,
                        links TEXT,
                        metadata TEXT,
                        extracted_at TEXT,
                        content_hash TEXT,
                        file_path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for faster queries
                if self.config.indexing:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON scraped_content(url)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON scraped_content(title)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags ON scraped_content(tags)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracted_at ON scraped_content(extracted_at)")
                
                conn.commit()
                
            logging.info("🗄️ Database initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize database: {e}")
    
    def save_json(self, data: Union[Dict, List], filename: str = None) -> str:
        """
        💾 Save data as JSON file
        """
        try:
            with self.lock:
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"scraped_data_{timestamp}.json"
                
                file_path = self.json_path / filename
                
                # Create backup if enabled
                if self.config.backup and file_path.exists():
                    self._create_backup(file_path)
                
                # Save data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
                # Compress if enabled
                if self.config.compress:
                    self._compress_file(file_path)
                
                logging.info(f"💾 JSON data saved: {file_path}")
                return str(file_path)
                
        except Exception as e:
            logging.error(f"❌ Failed to save JSON data: {e}")
            return ""
    
    def save_csv(self, data: List[Dict], filename: str = None) -> str:
        """
        📊 Save data as CSV file
        """
        try:
            with self.lock:
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"scraped_data_{timestamp}.csv"
                
                file_path = self.csv_path / filename
                
                # Create backup if enabled
                if self.config.backup and file_path.exists():
                    self._create_backup(file_path)
                
                if data:
                    # Flatten nested data for CSV
                    flattened_data = self._flatten_data(data)
                    
                    # Write CSV
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                        writer.writeheader()
                        writer.writerows(flattened_data)
                
                # Compress if enabled
                if self.config.compress:
                    self._compress_file(file_path)
                
                logging.info(f"📊 CSV data saved: {file_path}")
                return str(file_path)
                
        except Exception as e:
            logging.error(f"❌ Failed to save CSV data: {e}")
            return ""
    
    def save_sqlite(self, data: Union[Dict, List], table_name: str = "scraped_content") -> bool:
        """
        🗄️ Save data to SQLite database
        """
        try:
            with self.lock:
                db_file = self.db_path / "scraped_data.db"
                
                with sqlite3.connect(db_file) as conn:
                    cursor = conn.cursor()
                    
                    if isinstance(data, dict):
                        data = [data]
                    
                    for item in data:
                        # Convert dataclass to dict if needed
                        if hasattr(item, '__dict__'):
                            item = asdict(item)
                        
                        # Prepare data for insertion
                        insert_data = self._prepare_sqlite_data(item)
                        
                        # Insert or update
                        cursor.execute(f"""
                            INSERT OR REPLACE INTO {table_name} 
                            (url, title, content, summary, author, publish_date, tags, entities, 
                             sentiment, language, word_count, reading_time, images, links, 
                             metadata, extracted_at, content_hash, file_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            insert_data.get('url', ''),
                            insert_data.get('title', ''),
                            insert_data.get('content', ''),
                            insert_data.get('summary', ''),
                            insert_data.get('author', ''),
                            insert_data.get('publish_date', ''),
                            json.dumps(insert_data.get('tags', [])),
                            json.dumps(insert_data.get('entities', {})),
                            insert_data.get('sentiment', ''),
                            insert_data.get('language', ''),
                            insert_data.get('word_count', 0),
                            insert_data.get('reading_time', 0),
                            json.dumps(insert_data.get('images', [])),
                            json.dumps(insert_data.get('links', [])),
                            json.dumps(insert_data.get('metadata', {})),
                            insert_data.get('extracted_at', ''),
                            insert_data.get('content_hash', ''),
                            insert_data.get('file_path', '')
                        ))
                    
                    conn.commit()
                
                logging.info(f"🗄️ SQLite data saved: {len(data)} records")
                return True
                
        except Exception as e:
            logging.error(f"❌ Failed to save SQLite data: {e}")
            return False
    
    def save_pickle(self, data: Any, filename: str = None) -> str:
        """
        🥒 Save data as pickle file
        """
        try:
            with self.lock:
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"scraped_data_{timestamp}.pkl"
                
                file_path = self.base_path / filename
                
                # Create backup if enabled
                if self.config.backup and file_path.exists():
                    self._create_backup(file_path)
                
                # Save data
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
                
                # Compress if enabled
                if self.config.compress:
                    self._compress_file(file_path)
                
                logging.info(f"🥒 Pickle data saved: {file_path}")
                return str(file_path)
                
        except Exception as e:
            logging.error(f"❌ Failed to save pickle data: {e}")
            return ""
    
    def save_parquet(self, data: List[Dict], filename: str = None) -> str:
        """
        🚀 Save data as Parquet file (for large datasets)
        """
        try:
            with self.lock:
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"scraped_data_{timestamp}.parquet"
                
                file_path = self.base_path / filename
                
                # Create backup if enabled
                if self.config.backup and file_path.exists():
                    self._create_backup(file_path)
                
                if data:
                    # Convert to DataFrame
                    df = pd.DataFrame(data)
                    
                    # Save as Parquet
                    df.to_parquet(file_path, index=False, compression='snappy')
                
                logging.info(f"🚀 Parquet data saved: {file_path}")
                return str(file_path)
                
        except Exception as e:
            logging.error(f"❌ Failed to save Parquet data: {e}")
            return ""
    
    def load_json(self, filename: str) -> Optional[Union[Dict, List]]:
        """
        📖 Load data from JSON file
        """
        try:
            file_path = self.json_path / filename
            
            # Check for compressed version
            if not file_path.exists() and self.config.compress:
                compressed_path = file_path.with_suffix('.json.gz')
                if compressed_path.exists():
                    file_path = compressed_path
            
            if file_path.exists():
                if file_path.suffix == '.gz':
                    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            return None
            
        except Exception as e:
            logging.error(f"❌ Failed to load JSON data: {e}")
            return None
    
    def load_csv(self, filename: str) -> Optional[List[Dict]]:
        """
        📊 Load data from CSV file
        """
        try:
            file_path = self.csv_path / filename
            
            # Check for compressed version
            if not file_path.exists() and self.config.compress:
                compressed_path = file_path.with_suffix('.csv.gz')
                if compressed_path.exists():
                    file_path = compressed_path
            
            if file_path.exists():
                if file_path.suffix == '.gz':
                    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        return list(reader)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        return list(reader)
            
            return None
            
        except Exception as e:
            logging.error(f"❌ Failed to load CSV data: {e}")
            return None
    
    def query_sqlite(self, query: str, params: tuple = ()) -> List[Dict]:
        """
        🔍 Query SQLite database
        """
        try:
            db_file = self.db_path / "scraped_data.db"
            
            with sqlite3.connect(db_file) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logging.error(f"❌ Failed to query database: {e}")
            return []
    
    def search_content(self, search_term: str, limit: int = 100) -> List[Dict]:
        """
        🔍 Search content in database
        """
        query = """
            SELECT * FROM scraped_content 
            WHERE title LIKE ? OR content LIKE ? OR summary LIKE ? OR tags LIKE ?
            ORDER BY extracted_at DESC
            LIMIT ?
        """
        
        search_pattern = f"%{search_term}%"
        return self.query_sqlite(query, (search_pattern, search_pattern, search_pattern, search_pattern, limit))
    
    def get_recent_content(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """
        📅 Get recent content
        """
        query = """
            SELECT * FROM scraped_content 
            WHERE datetime(extracted_at) > datetime('now', '-{} days')
            ORDER BY extracted_at DESC
            LIMIT ?
        """.format(days)
        
        return self.query_sqlite(query, (limit,))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        📊 Get storage statistics
        """
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'json_files': 0,
                'csv_files': 0,
                'db_size': 0,
                'backup_files': 0
            }
            
            # Count files and calculate sizes
            for path in [self.json_path, self.csv_path, self.base_path]:
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        stats['total_files'] += 1
                        stats['total_size'] += file_path.stat().st_size
                        
                        if path == self.json_path:
                            stats['json_files'] += 1
                        elif path == self.csv_path:
                            stats['csv_files'] += 1
            
            # Database size
            db_file = self.db_path / "scraped_data.db"
            if db_file.exists():
                stats['db_size'] = db_file.stat().st_size
            
            # Backup files
            stats['backup_files'] = len(list(self.backup_path.rglob('*')))
            
            # Database record count
            count_result = self.query_sqlite("SELECT COUNT(*) as count FROM scraped_content")
            stats['total_records'] = count_result[0]['count'] if count_result else 0
            
            return stats
            
        except Exception as e:
            logging.error(f"❌ Failed to get stats: {e}")
            return {}
    
    def cleanup_old_files(self, days: int = None):
        """
        🧹 Cleanup old files
        """
        try:
            days = days or self.config.cleanup_days
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            cleaned_count = 0
            
            for path in [self.json_path, self.csv_path, self.base_path]:
                for file_path in path.rglob('*'):
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_date:
                        file_path.unlink()
                        cleaned_count += 1
            
            logging.info(f"🧹 Cleaned up {cleaned_count} old files")
            
        except Exception as e:
            logging.error(f"❌ Failed to cleanup files: {e}")
    
    def _flatten_data(self, data: List[Dict]) -> List[Dict]:
        """Flatten nested data for CSV export"""
        flattened = []
        
        for item in data:
            flat_item = {}
            
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    flat_item[key] = json.dumps(value)
                else:
                    flat_item[key] = str(value) if value is not None else ''
            
            flattened.append(flat_item)
        
        return flattened
    
    def _prepare_sqlite_data(self, data: Dict) -> Dict:
        """Prepare data for SQLite insertion"""
        prepared = {}
        
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                prepared[key] = json.dumps(value)
            else:
                prepared[key] = str(value) if value is not None else ''
        
        return prepared
    
    def _create_backup(self, file_path: Path):
        """Create backup of existing file"""
        try:
            backup_file = self.backup_path / f"{file_path.name}.backup"
            shutil.copy2(file_path, backup_file)
        except Exception as e:
            logging.warning(f"⚠️ Failed to create backup: {e}")
    
    def _compress_file(self, file_path: Path):
        """Compress file with gzip"""
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            file_path.unlink()
            
        except Exception as e:
            logging.warning(f"⚠️ Failed to compress file: {e}")

# Convenience functions
def save_json(data: Union[Dict, List], filename: str = None, config: StorageConfig = None) -> str:
    """Quick save JSON function"""
    storage = DataStorage(config)
    return storage.save_json(data, filename)

def save_csv(data: List[Dict], filename: str = None, config: StorageConfig = None) -> str:
    """Quick save CSV function"""
    storage = DataStorage(config)
    return storage.save_csv(data, filename)

def save_sqlite(data: Union[Dict, List], config: StorageConfig = None) -> bool:
    """Quick save SQLite function"""
    storage = DataStorage(config)
    return storage.save_sqlite(data)

def load_json(filename: str, config: StorageConfig = None) -> Optional[Union[Dict, List]]:
    """Quick load JSON function"""
    storage = DataStorage(config)
    return storage.load_json(filename)

def search_content(search_term: str, config: StorageConfig = None, limit: int = 100) -> List[Dict]:
    """Quick search function"""
    storage = DataStorage(config)
    return storage.search_content(search_term, limit)

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test storage system
    config = StorageConfig(
        base_path="test_data",
        format="json",
        compress=False,
        backup=True
    )
    
    storage = DataStorage(config)
    
    # Test data
    test_data = [
        {
            "url": "https://example.com/article1",
            "title": "AI Revolution in Web Scraping",
            "content": "Artificial Intelligence is transforming web scraping...",
            "summary": "AI is revolutionizing web scraping with advanced NLP models.",
            "tags": ["ai", "web-scraping", "nlp"],
            "word_count": 150,
            "extracted_at": datetime.now().isoformat()
        },
        {
            "url": "https://example.com/article2",
            "title": "Advanced Browser Automation",
            "content": "Modern web scraping requires sophisticated browser automation...",
            "summary": "Browser automation techniques for dynamic content extraction.",
            "tags": ["automation", "browser", "playwright"],
            "word_count": 200,
            "extracted_at": datetime.now().isoformat()
        }
    ]
    
    # Test JSON saving
    print("💾 Testing JSON storage...")
    json_file = storage.save_json(test_data)
    print(f"JSON saved: {json_file}")
    
    # Test CSV saving
    print("\n📊 Testing CSV storage...")
    csv_file = storage.save_csv(test_data)
    print(f"CSV saved: {csv_file}")
    
    # Test SQLite saving
    print("\n🗄️ Testing SQLite storage...")
    sqlite_success = storage.save_sqlite(test_data)
    print(f"SQLite saved: {sqlite_success}")
    
    # Test loading
    print("\n📖 Testing data loading...")
    loaded_json = storage.load_json(os.path.basename(json_file))
    print(f"Loaded JSON records: {len(loaded_json) if loaded_json else 0}")
    
    # Test search
    print("\n🔍 Testing search...")
    search_results = storage.search_content("AI")
    print(f"Search results: {len(search_results)}")
    
    # Test stats
    print("\n📊 Testing stats...")
    stats = storage.get_stats()
    print(f"Storage stats: {stats}")
    
    print("\n💾 Storage Engine initialized successfully!")
