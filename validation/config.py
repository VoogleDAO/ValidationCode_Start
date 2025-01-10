class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'your-secret-key'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    pass

class TestingConfig(Config):
    TESTING = True
