from requests import get
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional
import csv


class HomeAssistantDatabase:
    """
    Class to manage SQLite database operations for Home Assistant entity history.
    """
    
    def __init__(self, db_path: str = "home_assistant_history.db"):
        """
        Initialize the database connection and create tables if they don't exist.
        
        :param db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create the database table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    state TEXT,
                    last_changed TEXT,
                    last_updated TEXT,
                    timestamp TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(entity_id, last_updated) ON CONFLICT IGNORE
                )
            ''')
            
            # Create index for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_entity_id_timestamp 
                ON entity_history(entity_id, last_updated)
            ''')
            conn.commit()
    
    def insert_entity_data(self, entity_data: List[Dict[str, Any]]) -> int:
        """
        Insert entity history data into the database.
        
        :param entity_data: List of entity state dictionaries
        :return: Number of records inserted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            records_inserted = 0
            
            for state_entry in entity_data:
                cursor.execute('''
                    INSERT OR IGNORE INTO entity_history 
                    (entity_id, state, last_changed, last_updated, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    state_entry.get("entity_id", ""),
                    state_entry.get("state", ""),
                    state_entry.get("last_changed", ""),
                    state_entry.get("last_updated", ""),
                    state_entry.get("last_updated", "")
                ))
                records_inserted += cursor.rowcount
            
            conn.commit()
            return records_inserted
    
    def get_entity_history(self, entity_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve entity history from the database.
        
        :param entity_id: The entity ID to query
        :param limit: Optional limit on number of records to return
        :return: List of entity history records
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM entity_history 
                WHERE entity_id = ? 
                ORDER BY last_updated DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query, (entity_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_entities(self) -> List[str]:
        """
        Get list of all unique entity IDs in the database.
        
        :return: List of entity IDs
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT entity_id FROM entity_history ORDER BY entity_id')
            return [row[0] for row in cursor.fetchall()]
    
    def export_to_csv(self, entity_id: str, filename: Optional[str] = None) -> str:
        """
        Export entity history to CSV file.
        
        :param entity_id: The entity ID to export
        :param filename: Optional custom filename
        :return: The filename of the exported CSV
        """        
        if not filename:
            safe_entity_name = entity_id.replace(".", "_").replace("/", "_")
            filename = f"home_assistant_{safe_entity_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        data = self.get_entity_history(entity_id)
        
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            if data:
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        return filename
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the database.
        
        :return: Dictionary with database statistics
        """
        with sqlite3.connect(self.db_path) as conn: 
            cursor = conn.cursor()
            
            # Total records
            cursor.execute('SELECT COUNT(*) FROM entity_history')
            total_records = cursor.fetchone()[0]
            
            # Unique entities
            cursor.execute('SELECT COUNT(DISTINCT entity_id) FROM entity_history')
            unique_entities = cursor.fetchone()[0]
            
            # Date range
            cursor.execute('SELECT MIN(last_updated), MAX(last_updated) FROM entity_history')
            date_range = cursor.fetchone()
            
            return {
                'total_records': total_records,
                'unique_entities': unique_entities,
                'earliest_record': date_range[0],
                'latest_record': date_range[1]
            }


class HomeAssistantAPI:
    """
    Class to handle Home Assistant API interactions.
    """
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize the API client.
        
        :param base_url: Base URL of the Home Assistant instance
        :param token: Bearer token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.valid_status_codes = [200, 201]
        self.db = HomeAssistantDatabase()
    
    def fetch_and_store_history(self, entity_id: str) -> bool:
        """
        Fetch entity history from Home Assistant API and store in database.
        
        :param entity_id: The entity ID to fetch history for
        :return: True if successful, False otherwise
        """
        url = f"{self.base_url}/api/history/period?filter_entity_id={entity_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }

        print(f"Fetching data for entity: {entity_id}")
        print(f"URL: {url}")
        
        try:
            response = get(url, headers=headers)

            # Check if the request was successful
            if response.status_code not in self.valid_status_codes:
                print(f"Error fetching data for {entity_id}: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False

            # Parse the JSON response
            data = response.json()
            
            # Check if data is empty
            if not data or (isinstance(data, list) and len(data) == 0):
                print(f"No data found for entity: {entity_id}")
                return False

            # Store data in database
            total_inserted = 0
            for entity_data in data:
                records_inserted = self.db.insert_entity_data(entity_data)
                total_inserted += records_inserted

            print(f"Data stored in database for entity: {entity_id}")
            print(f"Total new records inserted: {total_inserted}")
            return True
            
        except Exception as e:
            print(f"Error processing entity {entity_id}: {str(e)}")
            return False


def main():
    """Main function to demonstrate usage."""
    load_dotenv()
    token = os.getenv("token")
    
    if not token:
        print("Error: No token found in environment variables")
        return
    
    # Initialize API client
    api = HomeAssistantAPI("http://192.168.1.102:8123", token)
    
    # Fetch and store history for multiple entities
    entities = ["sensor.meter_voltage_r", "sensor.ac_active_power"]
    
    for entity_id in entities:
        success = api.fetch_and_store_history(entity_id)
        if success:
            print(f"✓ Successfully processed {entity_id}")
        else:
            print(f"✗ Failed to process {entity_id}")
        print("-" * 50)
    
    # Display database statistics
    stats = api.db.get_database_stats()
    print("\nDatabase Statistics:")
    print(f"Total records: {stats['total_records']}")
    print(f"Unique entities: {stats['unique_entities']}")
    print(f"Date range: {stats['earliest_record']} to {stats['latest_record']}")
    
    # List all entities in database
    entities_in_db = api.db.get_all_entities()
    print(f"\nEntities in database: {entities_in_db}")

if __name__ == "__main__":
    main()

