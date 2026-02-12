from sqlalchemy import func, extract
from app.models import db

def get_hour_extract(column):
    """
    Returns the dialect-specific expression to extract the hour.
    Casts to Integer for cross-database consistency.
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.cast(func.strftime('%H', column), db.Integer)
    return func.cast(extract('hour', column), db.Integer)

def get_dow_extract(column):
    """
    Returns the dialect-specific expression to extract the day of week (0-6).
    PostgreSQL: 'dow' (0=Sunday)
    SQLite: '%w' (0=Sunday)
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.cast(func.strftime('%w', column), db.Integer)
    return func.cast(extract('dow', column), db.Integer)

def get_year_extract(column):
    """
    Returns the dialect-specific expression to extract the year.
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.cast(func.strftime('%Y', column), db.Integer)
    return func.cast(extract('year', column), db.Integer)

def get_month_extract(column):
    """
    Returns the dialect-specific expression to extract the month (1-12).
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.cast(func.strftime('%m', column), db.Integer)
    return func.cast(extract('month', column), db.Integer)
