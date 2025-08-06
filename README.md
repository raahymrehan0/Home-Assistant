# Home Assistant History Database

A Python application that fetches entity history data from Home Assistant and stores it in a SQLite database for persistent storage, analysis, and export capabilities.

## Features

- **SQLite Database Storage**: Persistent storage of Home Assistant entity history
- **Duplicate Prevention**: Automatic handling of duplicate records with unique constraints
- **Class-based Architecture**: Clean, maintainable code with separate classes for database and API operations
- **CSV Export**: Export any entity's history to CSV format
- **Database Statistics**: Get insights about your stored data
- **Error Handling**: Robust error handling for API requests and database operations
- **Indexing**: Optimized database queries with proper indexing

## Requirements

- Python 3.7+
- Home Assistant instance with API access
- Bearer token for Home Assistant API authentication

## Dependencies

```bash
pip install requests python-dotenv
```

## Setup

1. **Clone or download** the project files
2. **Create a `.env` file** in the project directory with your Home Assistant token:
   ```
   token=your_home_assistant_bearer_token_here
   ```
3. **Update the Home Assistant URL** in the `main()` function if different from `http://192.168.1.102:8123`

## Usage

### Basic Usage

Run the script to fetch and store history for the default entities:

```bash
python history.py
```

### Programmatic Usage

```python
from history import HomeAssistantAPI, HomeAssistantDatabase

# Initialize API client
api = HomeAssistantAPI("http://your-homeassistant-url:8123", "your_bearer_token")

# Fetch and store data for a specific entity
success = api.fetch_and_store_history("sensor.temperature")

# Access the database directly
db = api.db

# Get entity history
history = db.get_entity_history("sensor.temperature", limit=100)

# Export to CSV
csv_file = db.export_to_csv("sensor.temperature")

# Get database statistics
stats = db.get_database_stats()
print(f"Total records: {stats['total_records']}")
```

## Database Schema

The SQLite database contains a single table `entity_history` with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing unique identifier |
| entity_id | TEXT | Home Assistant entity ID |
| state | TEXT | Entity state value |
| last_changed | TEXT | Timestamp when entity last changed |
| last_updated | TEXT | Timestamp when entity was last updated |
| timestamp | TEXT | Duplicate of last_updated for compatibility |
| created_at | TIMESTAMP | When record was inserted into database |

### Unique Constraint
- `(entity_id, last_updated)` - Prevents duplicate records for the same entity at the same timestamp

### Indexes
- `idx_entity_id_timestamp` - Optimizes queries by entity_id and timestamp

## Classes

### HomeAssistantDatabase

Manages all SQLite database operations.

**Key Methods:**
- `insert_entity_data(entity_data)` - Insert entity history data
- `get_entity_history(entity_id, limit=None)` - Retrieve entity history
- `get_all_entities()` - Get list of all entities in database
- `export_to_csv(entity_id, filename=None)` - Export entity data to CSV
- `get_database_stats()` - Get database statistics

### HomeAssistantAPI

Handles Home Assistant API interactions and integrates with the database.

**Key Methods:**
- `fetch_and_store_history(entity_id)` - Fetch from API and store in database

## Configuration

### Environment Variables

Create a `.env` file with:
```
token=your_home_assistant_long_lived_access_token
```

### Customizing Entities

Edit the `entities` list in the `main()` function:

```python
entities = [
    "sensor.meter_voltage_r",
    "sensor.ac_active_power",
    "sensor.your_custom_entity"
]
```

### Custom Database Path

```python
# Use custom database file
api = HomeAssistantAPI("http://your-url:8123", token)
api.db = HomeAssistantDatabase("custom_path/my_database.db")
```

## Output Examples

### Console Output
```
Fetching data for entity: sensor.meter_voltage_r
URL: http://192.168.1.102:8123/api/history/period?filter_entity_id=sensor.meter_voltage_r
Data stored in database for entity: sensor.meter_voltage_r
Total new records inserted: 245
✓ Successfully processed sensor.meter_voltage_r
--------------------------------------------------

Database Statistics:
Total records: 490
Unique entities: 2
Date range: 2025-07-22T10:30:00.000000+00:00 to 2025-07-23T08:45:30.000000+00:00

Entities in database: ['sensor.ac_active_power', 'sensor.meter_voltage_r']
```

## Error Handling

The application handles various error scenarios:

- **Invalid API tokens**: Clear error messages for authentication failures
- **Network issues**: Graceful handling of connection problems
- **Empty responses**: Proper handling when no data is available
- **Database errors**: SQLite connection and query error handling
- **Duplicate data**: Automatic prevention of duplicate records

## Data Analysis Examples

### Query Recent Data
```python
# Get last 24 hours of data (assuming you run this daily)
recent_data = db.get_entity_history("sensor.temperature", limit=24)
```

### Export for Analysis
```python
# Export all data for external analysis
csv_file = db.export_to_csv("sensor.power_consumption")
print(f"Data exported to: {csv_file}")
```

### Database Statistics
```python
stats = db.get_database_stats()
print(f"Monitoring {stats['unique_entities']} entities")
print(f"Data spans from {stats['earliest_record']} to {stats['latest_record']}")
```

## Scheduling

To automatically collect data at regular intervals, you can use:

### Cron (Linux/macOS)
```bash
# Run every hour
0 * * * * cd /path/to/project && python history.py
```

### Task Scheduler (Windows)
Create a scheduled task to run `python history.py` at your desired interval.

### Python Scheduler
```python
import schedule
import time

def job():
    # Your data collection logic here
    api = HomeAssistantAPI("http://192.168.1.102:8123", token)
    for entity_id in ["sensor.temperature", "sensor.humidity"]:
        api.fetch_and_store_history(entity_id)

schedule.every().hour.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Feel free to use and modify as needed.

## Troubleshooting

### Common Issues

1. **"No token found in environment variables"**
   - Ensure your `.env` file exists and contains the token
   - Check that the token is valid in Home Assistant

2. **"Error fetching data: HTTP 401"**
   - Your bearer token may be invalid or expired
   - Generate a new long-lived access token in Home Assistant

3. **"No data found for entity"**
   - Verify the entity ID exists in your Home Assistant instance
   - Check that the entity has historical data

4. **Database locked errors**
   - Ensure no other processes are accessing the database file
   - The application uses context managers to properly close connections

### Getting Home Assistant Bearer Token

1. Go to your Home Assistant web interface
2. Click on your profile (bottom left)
3. Scroll down to "Long-lived access tokens"
4. Click "Create Token"
5. Give it a name and copy the generated token
6. Add it to your `.env` file

## Future Enhancements

- Data visualization with matplotlib/plotly
- Real-time data streaming
- Data aggregation and analytics
- Web dashboard interface
- Support for multiple Home Assistant instances
- Data retention policies
- Backup and restore functionality
