"""
Database setup and models for Heliotelligence
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Module(Base):
    """Solar module database model"""
    __tablename__ = 'modules'
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(255), unique=True, index=True, nullable=False)
    pdc0 = Column(Float, nullable=False)  # Power rating at STC (W)
    gamma_pdc = Column(Float, nullable=False)  # Temperature coefficient (%/°C)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Inverter(Base):
    """Inverter database model"""
    __tablename__ = 'inverters'
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(255), unique=True, index=True, nullable=False)
    pdc0 = Column(Float, nullable=False)  # Power rating (W)
    eta_inv_nom = Column(Float, nullable=False)  # Nominal efficiency (%)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./heliotelligence.db")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def populate_sample_data():
    """Populate database with sample module and inverter data"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Module).count() > 0:
            print("Sample data already exists, skipping population")
            return
        
        # Sample solar modules
        sample_modules = [
            {"model_name": "Canadian Solar CS3W-400P", "pdc0": 400, "gamma_pdc": -0.37},
            {"model_name": "JinkoSolar JKM400M-72H", "pdc0": 400, "gamma_pdc": -0.35},
            {"model_name": "Trina Solar TSM-DE06M.08(II)", "pdc0": 405, "gamma_pdc": -0.34},
            {"model_name": "LONGi Solar LR4-72HPH-450M", "pdc0": 450, "gamma_pdc": -0.35},
            {"model_name": "Q CELLS Q.PEAK DUO BLK ML-G10+ 400", "pdc0": 400, "gamma_pdc": -0.35},
            {"model_name": "SunPower SPR-X22-370", "pdc0": 370, "gamma_pdc": -0.29},
            {"model_name": "Panasonic VBHN330SA17", "pdc0": 330, "gamma_pdc": -0.26},
            {"model_name": "First Solar FS-6445A", "pdc0": 445, "gamma_pdc": -0.28},
        ]
        
        # Sample inverters
        sample_inverters = [
            {"model_name": "SMA Sunny Tripower 25000TL", "pdc0": 25000, "eta_inv_nom": 98.1},
            {"model_name": "Fronius Symo 20.0-3-M", "pdc0": 20000, "eta_inv_nom": 97.9},
            {"model_name": "ABB TRIO-27.6-TL-OUTD", "pdc0": 27600, "eta_inv_nom": 98.0},
            {"model_name": "Huawei SUN2000-50KTL-M0", "pdc0": 50000, "eta_inv_nom": 98.6},
            {"model_name": "SolarEdge SE27.6K-RW000BNF4", "pdc0": 27600, "eta_inv_nom": 97.5},
            {"model_name": "Sungrow SG50CX", "pdc0": 50000, "eta_inv_nom": 98.5},
            {"model_name": "FIMER PVS-100-TL", "pdc0": 100000, "eta_inv_nom": 98.7},
            {"model_name": "Delta RPI M50A", "pdc0": 50000, "eta_inv_nom": 98.2},
        ]
        
        # Add modules
        for module_data in sample_modules:
            module = Module(**module_data)
            db.add(module)
        
        # Add inverters
        for inverter_data in sample_inverters:
            inverter = Inverter(**inverter_data)
            db.add(inverter)
        
        db.commit()
        print(f"Successfully added {len(sample_modules)} modules and {len(sample_inverters)} inverters")
        
    except Exception as e:
        db.rollback()
        print(f"Error populating sample data: {e}")
        raise
    finally:
        db.close()


# PostgreSQL schema for AWS RDS deployment
POSTGRESQL_SCHEMA = """
-- PostgreSQL schema for AWS RDS deployment

CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) UNIQUE NOT NULL,
    pdc0 FLOAT NOT NULL,  -- Power rating at STC (W)
    gamma_pdc FLOAT NOT NULL,  -- Temperature coefficient (%/°C)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_modules_model_name ON modules(model_name);

CREATE TABLE inverters (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) UNIQUE NOT NULL,
    pdc0 FLOAT NOT NULL,  -- Power rating (W)
    eta_inv_nom FLOAT NOT NULL,  -- Nominal efficiency (%)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inverters_model_name ON inverters(model_name);

-- Sample data insertion
INSERT INTO modules (model_name, pdc0, gamma_pdc) VALUES
('Canadian Solar CS3W-400P', 400, -0.37),
('JinkoSolar JKM400M-72H', 400, -0.35),
('Trina Solar TSM-DE06M.08(II)', 405, -0.34),
('LONGi Solar LR4-72HPH-450M', 450, -0.35),
('Q CELLS Q.PEAK DUO BLK ML-G10+ 400', 400, -0.35),
('SunPower SPR-X22-370', 370, -0.29),
('Panasonic VBHN330SA17', 330, -0.26),
('First Solar FS-6445A', 445, -0.28);

INSERT INTO inverters (model_name, pdc0, eta_inv_nom) VALUES
('SMA Sunny Tripower 25000TL', 25000, 98.1),
('Fronius Symo 20.0-3-M', 20000, 97.9),
('ABB TRIO-27.6-TL-OUTD', 27600, 98.0),
('Huawei SUN2000-50KTL-M0', 50000, 98.6),
('SolarEdge SE27.6K-RW000BNF4', 27600, 97.5),
('Sungrow SG50CX', 50000, 98.5),
('FIMER PVS-100-TL', 100000, 98.7),
('Delta RPI M50A', 50000, 98.2);
"""


if __name__ == "__main__":
    # Create tables and populate with sample data
    create_tables()
    populate_sample_data()
    print("Database setup completed!")

