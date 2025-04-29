"""
Skrypt do sprawdzenia struktury bazy danych i danych quizów
"""
import sqlite3
import json

# Połączenie z bazą danych
conn = sqlite3.connect('quiz_app.db')
cursor = conn.cursor()

# Wyświetl tabele
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:", [table[0] for table in tables])

# Sprawdź strukturę tabeli quizzes
cursor.execute("PRAGMA table_info(quizzes)")
columns = cursor.fetchall()
print("\nQuiz table structure:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

# Pobierz przykładowe dane quizu
cursor.execute("SELECT id, title, questions_json FROM quizzes LIMIT 1")
rows = cursor.fetchall()
print("\nSample quiz data:")
for row in rows:
    quiz_id = row[0]
    title = row[1]
    questions_json = row[2]
    
    print(f"ID: {quiz_id}")
    print(f"Title: {title}")
    
    # Parsuj JSON pytań
    try:
        questions = json.loads(questions_json)
        print(f"Questions count: {len(questions)}")
        print("\nSample questions structure:")
        
        # Wyświetl pierwsze pytanie
        if questions and len(questions) > 0:
            q1 = questions[0]
            print(json.dumps(q1, indent=2, ensure_ascii=False))
            
            # Sprawdź kluczowe pola pytania
            required_fields = ['question', 'options', 'correctAnswer']
            missing_fields = [field for field in required_fields if field not in q1]
            
            if missing_fields:
                print(f"\nWARNING: Missing required fields: {missing_fields}")
            else:
                print("\nAll required fields present!")
                
                # Sprawdź czy correctAnswer jest liczbą
                if not isinstance(q1['correctAnswer'], int):
                    print(f"WARNING: correctAnswer is not an integer! Type: {type(q1['correctAnswer'])}, Value: {q1['correctAnswer']}")
                
                # Sprawdź czy options jest listą
                if not isinstance(q1['options'], list):
                    print(f"WARNING: options is not a list! Type: {type(q1['options'])}")
                else:
                    print(f"Options count: {len(q1['options'])}")
                    
                    # Sprawdź czy correctAnswer jest w zakresie options
                    if q1['correctAnswer'] >= len(q1['options']) or q1['correctAnswer'] < 0:
                        print(f"WARNING: correctAnswer ({q1['correctAnswer']}) is out of range for options (0-{len(q1['options'])-1})!")
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in questions_json field!")
        print(f"Raw data: {questions_json[:200]}...")
    except Exception as e:
        print(f"ERROR: {str(e)}")

conn.close()
