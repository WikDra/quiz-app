"""
Setup script to create the MySQL database and tables.
Run this script before starting the Flask application.
"""
import os
import sys
import pymysql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_database():
    """Create the MySQL database if it doesn't exist"""
    # Extract database name from the connection string
    db_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/quiz_app_db')
    
    # Parse the connection string to get the database name and credentials
    parts = db_url.replace('mysql+pymysql://', '').split('/')
    credentials = parts[0].split('@')
    
    if ':' in credentials[0]:
        username, password = credentials[0].split(':')
    else:
        username, password = credentials[0], ''
    
    host = credentials[1].split(':')[0] if ':' in credentials[1] else credentials[1]
    port = int(credentials[1].split(':')[1]) if ':' in credentials[1] else 3306
    
    db_name = parts[1]
      # Connect to MySQL server without specifying a database
    try:
        # Użyj różnych metod połączenia
        # Metoda 1: Standardowe połączenie
        try:
            print("Próba połączenia metodą standardową...")
            conn = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                charset='utf8mb4'
            )
        except pymysql.MySQLError as e1:
            print(f"Standardowe połączenie nie powiodło się: {e1}")
            
            # Metoda 2: Użyj auth_plugin=mysql_native_password
            try:
                print("Próba połączenia z auth_plugin=mysql_native_password...")
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    charset='utf8mb4',
                    auth_plugin='mysql_native_password'
                )
            except pymysql.MySQLError as e2:
                print(f"Połączenie z mysql_native_password nie powiodło się: {e2}")
                
                # Metoda 3: Spróbuj połączenie do 'localhost' zamiast 127.0.0.1
                try:
                    if host == '127.0.0.1':
                        print("Próba połączenia przez socket...")
                        conn = pymysql.connect(
                            host='localhost',
                            port=port,
                            user=username,
                            password=password,
                            charset='utf8mb4'
                        )
                    else:
                        raise pymysql.MySQLError("Już próbowaliśmy połączenia z 'localhost'")
                except pymysql.MySQLError as e3:
                    print(f"Wszystkie metody połączenia nie powiodły się.")
                    raise e3
        
        with conn.cursor() as cursor:
            # Check if database exists
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
            result = cursor.fetchone()
            
            if not result:
                print(f"Creating database '{db_name}'...")
                cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                print(f"Database '{db_name}' created successfully!")
            else:
                print(f"Database '{db_name}' already exists.")
        
        conn.commit()
        conn.close()
        return True
        
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL server: {e}")
        return False

if __name__ == "__main__":
    print("Setting up the MySQL database...")
    if create_database():
        print("Database setup completed!")
        
        # Import Flask app and create tables
        try:
            from app import create_app, db
            app = create_app()
            
            with app.app_context():
                db.create_all()
                print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")
    else:
        print("Failed to set up the database.")
