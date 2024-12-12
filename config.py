import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = 'votre_clé_secrète'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///boutique.db'
    UPLOAD_FOLDER = 'static/images' 