import os

class Config:
    SECRET_KEY = "X9s$Kp3!qL8@zF2#WmR7"   #example key...you can enter any random string for this
    SQLALCHEMY_DATABASE_URI = "sqlite:///placement.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "static/uploads"