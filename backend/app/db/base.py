# Import all models here for SQLAlchemy's metadata
# This file is used for Alembic migrations and creating tables

from sqlalchemy.ext.declarative import declarative_base

# Base class for all models
Base = declarative_base()

# Import all models to register them with the Base metadata
# This ensures they are discovered by Alembic for migrations

# For example:
# from app.db.models.user import User
# from app.db.models.insight import Insight
