import os
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Setup Database in the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'awip.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DBExperiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String, index=True)
    task_type = Column(String)
    domain = Column(String)
    winner_model = Column(String)
    score = Column(Float)
    features_added = Column(Integer)
    key_issues = Column(JSON)
    workflow_dag = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class DBAgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, index=True) # links to experiments.id
    sender = Column(String, index=True)
    content = Column(String)
    confidence = Column(Integer, nullable=True)
    metadata_json = Column(JSON)
    timestamp = Column(String)

# Create tables
Base.metadata.create_all(bind=engine)
