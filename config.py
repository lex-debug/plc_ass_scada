import os

class Config:
    DEBUG = False
    DEVELOPMENT = False
    DB_HOST = os.getenv("DB_HOST", "this-is-default-host")
    DB_USER = os.getenv("DB_USER", "this-is-default-user")
    DB_PASS = os.getenv("DB_PASS", "this-is-default-pass")
    SECRET_KEY = os.getenv("SECRET_KEY", "this-is-the-default-key")

class ProductionConfig(Config):
    pass

class StagingConfig(Config):
    DEBUG = True

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True