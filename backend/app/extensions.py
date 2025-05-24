from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
import os

oauth2 = OAuth()
google = oauth2.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)
db = SQLAlchemy()
