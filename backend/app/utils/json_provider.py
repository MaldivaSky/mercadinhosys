
from flask.json.provider import DefaultJSONProvider
from decimal import Decimal
from datetime import date, datetime

class CustomJSONProvider(DefaultJSONProvider):
    """
    JSON Provider customizado para lidar com tipos do SQLAlchemy/Python
    que não são serializáveis por padrão (Decimal, date, datetime).
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)
