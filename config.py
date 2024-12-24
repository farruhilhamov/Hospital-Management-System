import os
# SECRET_KEY = os.urandom(32)
SECRET_KEY = "supersecretkey"
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_DATABASE_URI = 'sqlite:///project.db'
