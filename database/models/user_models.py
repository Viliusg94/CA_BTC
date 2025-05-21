"""
Naudotojų duomenų modeliai.
Šiame modulyje apibrėžiamos naudotojų ir su jais susijusių duomenų klasės.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Float, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from utils.id_generator import generate_session_id

# Sukuriame bazinę klasę modeliams
Base = declarative_base()

class User(Base):
    """
    Naudotojo duomenų modelis.
    Saugo pagrindinę informaciją apie sistemos naudotojus.
    """
    # Lentelės pavadinimas duomenų bazėje
    __tablename__ = "users"

    # Stulpeliai (lentelės laukai)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Ryšiai su kitomis lentelėmis
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    metrics = relationship("UserMetrics", back_populates="user", cascade="all, delete-orphan")
    model_metrics = relationship("ModelMetrics", back_populates="user")
    # Pridedame ryšį su naudotojo metrikomis
    # Vienas naudotojas gali turėti daug metrikų, kurios bus ištrintos kartu su naudotoju
    user_metrics = relationship("UserMetric", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        """
        Grąžina objekto tekstinę reprezentaciją.
        """
        return f"<User {self.username}>"

class UserSession(Base):
    """
    Naudotojo sesijos duomenų modelis.
    Saugo informaciją apie naudotojų sesijas sistemoje.
    """
    # Lentelės pavadinimas duomenų bazėje
    __tablename__ = "user_sessions"

    # Stulpeliai (lentelės laukai)
    id = Column(String(36), primary_key=True, default=lambda: generate_session_id())
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_type = Column(String(20), nullable=False, comment="Sesijos tipas (training/testing/general)")
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), default="active", nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_metadata = Column(JSON, nullable=True, comment="Papildoma informacija apie sesiją (JSON)")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Ryšiai su kitomis lentelėmis
    user = relationship("User", back_populates="sessions")
    training_session = relationship("TrainingSession", back_populates="session", uselist=False, cascade="all, delete-orphan")
    testing_session = relationship("TestingSession", back_populates="session", uselist=False, cascade="all, delete-orphan")
    metrics = relationship("UserMetrics", back_populates="session")
    session_metrics = relationship("SessionMetrics", back_populates="session", cascade="all, delete-orphan")
    # Pridedame ryšį su sesijos metrikomis
    # Viena sesija gali turėti daug metrikų, kurios bus ištrintos kartu su sesija
    metrics = relationship("SessionMetric", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        """
        Grąžina objekto tekstinę reprezentaciją.
        """
        status_info = f"active" if self.is_active else f"ended at {self.end_time}"
        return f"<UserSession {self.id} ({self.session_type}) - {status_info}>"
        
class TrainingSession(Base):
    """
    Modelio treniravimo sesijos duomenų modelis.
    Saugo specifinius duomenis, susijusius su modelių treniravimo sesijomis.
    """
    # Lentelės pavadinimas duomenų bazėje
    __tablename__ = "training_sessions"

    # Stulpeliai (lentelės laukai)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    model_id = Column(String(36), ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    dataset_name = Column(String(100), nullable=True)
    start_epoch = Column(Integer, default=0)
    total_epochs = Column(Integer, nullable=True)
    current_epoch = Column(Integer, default=0)
    learning_rate = Column(Float, nullable=True)
    batch_size = Column(Integer, nullable=True)
    loss_function = Column(String(50), nullable=True)
    validation_split = Column(Float, default=0.2)
    early_stopping = Column(Boolean, default=False)
    checkpoint_enabled = Column(Boolean, default=False)
    training_status = Column(String(20), default="pending")  # pending, running, completed, failed, stopped
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Ryšiai su kitomis lentelėmis
    session = relationship("UserSession", back_populates="training_session")
    metrics = relationship("ModelMetrics", back_populates="training_session")

    def __repr__(self):
        """
        Grąžina objekto tekstinę reprezentaciją.
        """
        return f"<TrainingSession {self.id} (Model: {self.model_id})>"

class TestingSession(Base):
    """
    Modelio testavimo sesijos duomenų modelis.
    Saugo specifinius duomenis, susijusius su modelių testavimo sesijomis.
    """
    # Lentelės pavadinimas duomenų bazėje
    __tablename__ = "testing_sessions"

    # Stulpeliai (lentelės laukai)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    model_id = Column(String(36), ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    dataset_name = Column(String(100), nullable=True)
    test_type = Column(String(50), default="accuracy")  # accuracy, performance, compatibility
    test_params = Column(Text, nullable=True)  # JSON parametrai testui
    results = Column(Text, nullable=True)  # JSON rezultatai
    testing_status = Column(String(20), default="pending")  # pending, running, completed, failed
    success = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Ryšiai su kitomis lentelėmis
    session = relationship("UserSession", back_populates="testing_session")
    metrics = relationship("ModelMetrics", back_populates="testing_session")

    def __repr__(self):
        """
        Grąžina objekto tekstinę reprezentaciją.
        """
        return f"<TestingSession {self.id} (Model: {self.model_id})>"