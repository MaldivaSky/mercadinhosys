from sqlalchemy import func, extract
from app.models import db

def get_hour_extract(column):
    """
    Returns the dialect-specific expression to extract the hour from a timestamp column.
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.strftime('%H', column)
    return extract('hour', column)

def get_dow_extract(column):
    """
    Returns the dialect-specific expression to extract the day of week (0-6).
    PostgreSQL: 'dow' (0=Sunday)
    SQLite: '%w' (0=Sunday)
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.strftime('%w', column)
    return extract('dow', column)

def get_year_extract(column):
    """
    Returns the dialect-specific expression to extract the year.
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.strftime('%Y', column)
    return extract('year', column)

def get_month_extract(column):
    """
    Returns the dialect-specific expression to extract the month (1-12).
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.strftime('%m', column)
    return extract('month', column)
