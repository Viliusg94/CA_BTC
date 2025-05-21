"""
SQLAlchemy bazinės klasės apibrėžimas.
Šis modulis skirtas bendrai naudojamai Base klasei apibrėžti.
"""
from sqlalchemy.ext.declarative import declarative_base

# Sukuriame bazinę klasę modeliams
Base = declarative_base()