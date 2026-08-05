from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Date
from sqlalchemy.sql import func
from database import Base

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    media_type = Column(String(20), default="TV")  # TV, Radio, Online
    region = Column(String(50), default="São Paulo")

class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, index=True)
    channel_code = Column(String(50), ForeignKey("channels.code"), nullable=False)
    broadcast_date = Column(Date, nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    
    original_title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    harmonized_title = Column(String(255), nullable=True)
    proposed_harmonized_title = Column(String(255), nullable=True)
    
    category = Column(String(100), nullable=True)
    proposed_category = Column(String(100), nullable=True)
    repeat_code = Column(String(20), default="N")  # Y/N
    reconciliation_key = Column(String(100), nullable=True)
    
    # Reconciliação / Programme Before
    programme_before_title = Column(String(255), nullable=True)
    mismatch_type = Column(String(100), nullable=True)  # Title Mismatch, Category Mismatch, Time Offset, New
    
    is_new_programme = Column(Integer, default=0) # 1 se for do relatório de Novos Programas
    status = Column(String(50), default="New")  # New, Open, Accepted, Rejected, Feedback Submitted, Resolved, Closed
    delivery_cycle = Column(String(50), default="Initial Delivery")  # Initial Delivery, First Redelivery, Final Redelivery
    
    feedback_comments = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class SpotDifference(Base):
    __tablename__ = "spot_differences"

    id = Column(Integer, primary_key=True, index=True)
    channel_code = Column(String(50), ForeignKey("channels.code"), nullable=False)
    broadcast_date = Column(Date, nullable=False)
    delivery_cycle = Column(String(50), default="Initial Delivery")
    
    spot_title = Column(String(255), nullable=False)
    advertiser = Column(String(255), nullable=False)
    planned_time = Column(String(10), nullable=True)
    monitored_time = Column(String(10), nullable=True)
    
    discrepancy_type = Column(String(100), nullable=False)  # Timing Difference, Missing Spot, Additional Spot, Break Discrepancy
    status = Column(String(50), default="Open")  # New, Open, Accepted, Rejected, Feedback Submitted, Resolved, Closed
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class KpiMetric(Base):
    __tablename__ = "kpi_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # Feedback Activity, Workflow, Quality, AsRun, Spot Planning
    value = Column(Float, nullable=False)
    unit = Column(String(20), default="count")  # count, percentage, hours
    
    channel_code = Column(String(50), nullable=True)
    media_type = Column(String(20), default="TV")
    delivery_cycle = Column(String(50), default="Initial Delivery")
