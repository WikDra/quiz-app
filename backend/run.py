from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    host = os.getenv('BACKEND_HOST', 'localhost')
    port = int(os.getenv('BACKEND_PORT', 5000))
    app.run(debug=True, host=host, port=port)
    