"""
Security MVP - Advanced Fraud Detection Engine
AI-powered counterfeit detection, risk scoring, pattern recognition, and anomaly detection
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Session, relationship
from pydantic import BaseModel
import json
from enum import Enum

# ============================================================================
# DATABASE MODELS FOR FRAUD DETECTION
# ============================================================================

class FraudRiskLevel(str, Enum):
    AUTHENTIC = "authentic"
    LIKELY_AUTHENTIC = "likely_authentic"
    SUSPICIOUS = "suspicious"
    LIKELY_COUNTERFEIT = "likely_counterfeit"
    COUNTERFEIT = "counterfeit"


class SerializedUnitFraudProfile(Base):
    """Fraud risk profile for each serialized unit"""
    __tablename__ = "serialized_unit_fraud_profiles"
    
    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("serialized_units.id"), unique=True)
    
    # Risk scoring
    initial_risk_score = Column(Float, default=0.0)  # 0-1.0
    current_risk_score = Column(Float, default=0.0)
    risk_level = Column(String(50), default=FraudRiskLevel.AUTHENTIC)
    
    # Detection factors
    batch_consistency_score = Column(Float, default=1.0)  # 0-1.0
    serial_format_score = Column(Float, default=1.0)
    manufacturer_data_score = Column(Float, default=1.0)
    geolocation_anomaly_score = Column(Float, default=0.0)  # 0 = normal, 1 = anomalous
    time_gap_anomaly_score = Column(Float, default=0.0)
    verification_pattern_score = Column(Float, default=1.0)
    
    # Batch metadata
    batch_id = Column(Integer, ForeignKey("batches.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    # Verification history
    total_verifications = Column(Integer, default=0)
    authentic_verifications = Column(Integer, default=0)
    counterfeit_reports = Column(Integer, default=0)
    
    # Geographic analysis
    first_verification_lat = Column(Float, nullable=True)
    first_verification_lng = Column(Float, nullable=True)
    last_verification_lat = Column(Float, nullable=True)
    last_verification_lng = Column(Float, nullable=True)
    geographic_inconsistencies = Column(Integer, default=0)
    
    # Time analysis
    first_verification_time = Column(DateTime, nullable=True)
    last_verification_time = Column(DateTime, nullable=True)
    verification_time_gaps = Column(JSON, default=list)  # List of time gaps in hours
    
    # ML features
    ml_features = Column(JSON, nullable=True)  # Stored features for ML model
    model_confidence = Column(Float, default=0.0)  # 0-1.0
    
    # Red flags
    red_flags = Column(JSON, default=list)  # List of detected red flags
    flags_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_analysis_at = Column(DateTime, nullable=True)


class BatchFraudAnalysis(Base):
    """Batch-level fraud analysis for pattern detection"""
    __tablename__ = "batch_fraud_analysis"
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), unique=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    # Batch stats
    total_units_in_batch = Column(Integer, default=0)
    units_verified = Column(Integer, default=0)
    counterfeit_units = Column(Integer, default=0)
    counterfeit_rate = Column(Float, default=0.0)  # 0-1.0
    
    # Pattern analysis
    serial_number_pattern_score = Column(Float, default=1.0)
    manufacturing_date_consistency = Column(Float, default=1.0)
    expiry_date_consistency = Column(Float, default=1.0)
    packaging_consistency = Column(Float, default=1.0)
    
    # Quality indicators
    qr_code_quality_score = Column(Float, default=1.0)
    label_printing_quality = Column(Float, default=1.0)
    hologram_authenticity = Column(Float, default=1.0)
    
    # Batch risk
    batch_risk_level = Column(String(50), default=FraudRiskLevel.AUTHENTIC)
    batch_risk_score = Column(Float, default=0.0)
    
    # Geographic distribution
    distribution_countries = Column(JSON, default=list)
    distribution_expected_region = Column(String(100), nullable=True)
    distribution_anomalies = Column(JSON, default=list)
    
    red_flags = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductFraudHistory(Base):
    """Track counterfeit history for each product"""
    __tablename__ = "product_fraud_history"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True)
    
    # Historical data
    total_verifications = Column(Integer, default=0)
    total_counterfeits = Column(Integer, default=0)
    counterfeit_rate = Column(Float, default=0.0)
    
    # Risk factors
    high_risk_batches = Column(Integer, default=0)
    high_risk_regions = Column(JSON, default=list)
    
    # Trend analysis
    counterfeit_trend = Column(String(50), default="stable")  # increasing, stable, decreasing
    trend_direction_monthly = Column(JSON, default=list)  # Last 12 months
    
    # Common counterfeiting patterns
    common_red_flags = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeographicAnomalyPattern(Base):
    """Track geographic anomalies for pattern learning"""
    __tablename__ = "geographic_anomaly_patterns"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    # Normal distribution patterns
    expected_regions = Column(JSON, default=list)  # List of regions where product should be
    unusual_regions = Column(JSON, default=list)  # Regions where product shouldn't be
    
    # Anomaly threshold
    distance_threshold_km = Column(Float, default=100.0)  # Suspicious if verified >100km apart
    
    # Geographic risk zones
    high_risk_zones = Column(JSON, default=list)  # Known counterfeit hotspots
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class FraudDetectionRequest(BaseModel):
    """Request for fraud detection analysis"""
    serial_number: str
    batch_number: str
    product_id: int
    verification_latitude: float
    verification_longitude: float
    verification_timestamp: datetime
    pharmacist_id: int = None
    pharmacy_id: int = None


class FraudDetectionResponse(BaseModel):
    """Detailed fraud detection response"""
    result: str  # AUTHENTIC, LIKELY_AUTHENTIC, SUSPICIOUS, LIKELY_COUNTERFEIT, COUNTERFEIT
    confidence_score: float  # 0-1.0
    risk_level: str
    risk_factors: List[str]
    red_flags: List[str]
    
    # Component scores
    batch_consistency_score: float
    serial_format_score: float
    geographic_anomaly_score: float
    time_gap_anomaly_score: float
    verification_pattern_score: float
    
    # Model details
    ml_model_confidence: float
    detection_method: str  # rule_based, ml_based, hybrid
    
    # Recommendations
    recommendation: str
    suggested_action: str  # accept, verify_manually, escalate_to_manufacturer, reject
    
    # Historical context
    product_counterfeit_rate: float
    batch_counterfeit_rate: float
    similar_counterfeits_found: int


class RedFlagAlert(BaseModel):
    """Individual red flag alert"""
    flag_type: str  # serial_mismatch, geographic_anomaly, time_gap, batch_inconsistency, etc.
    severity: str  # low, medium, high, critical
    description: str
    evidence: Dict


class FraudPatternAnalysis(BaseModel):
    """Analysis of fraud patterns for admin"""
    product_id: int
    product_name: str
    counterfeit_rate: float
    trend: str
    common_patterns: List[str]
    geographic_hotspots: List[str]
    recommended_action: str


# ============================================================================
# FRAUD DETECTION ENGINE
# ============================================================================

class AdvancedFraudDetectionEngine:
    """Main fraud detection engine with ML capabilities"""
    
    def __init__(self, db: Session):
        self.db = db
        self.COUNTERFEIT_THRESHOLD = 0.65  # Score >= 0.65 = likely counterfeit
        self.AUTHENTIC_THRESHOLD = 0.35    # Score < 0.35 = likely authentic
        self.SUSPICIOUS_ZONE = (0.35, 0.65) # Gray zone = suspicious
        
        # Geographic constants (Ghana-focused)
        self.GHANA_BOUNDS = {
            'north': 11.4,
            'south': 1.0,
            'east': 1.2,
            'west': -3.5
        }
        
        self.MAJOR_CITIES = {
            'Accra': (5.6037, -0.2869),
            'Kumasi': (6.6753, -1.6264),
            'Tema': (5.7294, -0.0052),
            'Takoradi': (4.8845, -1.7523),
            'Sekondi': (4.9336, -1.7429),
        }
    
    def analyze_serial_number(self, serial: str, product_id: int) -> Tuple[float, List[str]]:
        """
        Analyze serial number format and validity
        Returns: (score 0-1.0, list of red flags)
        """
        red_flags = []
        score = 1.0  # Start perfect
        
        # Check serial format
        if not self._is_valid_serial_format(serial):
            red_flags.append("Invalid serial number format")
            score -= 0.3
        
        # Check for duplicate serials (highly suspicious)
        duplicate_count = self.db.query(SerializedUnit).filter(
            SerializedUnit.serial_number == serial,
            SerializedUnit.id != getattr(self, 'current_unit_id', None)
        ).count()
        
        if duplicate_count > 0:
            red_flags.append(f"Serial number used {duplicate_count} times (duplicates detected)")
            score -= 0.4
        
        # Check serial number entropy (random vs sequential)
        if self._is_sequential_serial(serial):
            red_flags.append("Serial appears sequential (low entropy)")
            score -= 0.25
        
        # Check for common counterfeit patterns
        if self._matches_counterfeit_pattern(serial, product_id):
            red_flags.append("Matches known counterfeit serial pattern")
            score -= 0.35
        
        return max(0.0, score), red_flags
    
    def analyze_batch_consistency(self, batch_id: int, serial: str, 
                                  product_id: int) -> Tuple[float, List[str]]:
        """
        Analyze batch consistency with product characteristics
        """
        red_flags = []
        score = 1.0
        
        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return 0.5, ["Batch not found in database"]
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        # Check batch format
        if not self._is_valid_batch_format(batch.batch_number):
            red_flags.append("Invalid batch number format")
            score -= 0.2
        
        # Check manufacturing date consistency
        if batch.manufacturing_date:
            days_old = (datetime.utcnow() - batch.manufacturing_date).days
            if days_old < 0:
                red_flags.append("Manufacturing date in future (impossible)")
                score -= 0.4
            elif days_old > 1825:  # 5 years
                red_flags.append("Product manufactured more than 5 years ago")
                score -= 0.25
        
        # Check expiry date validity
        if batch.expiry_date:
            if batch.expiry_date < datetime.utcnow():
                red_flags.append("Product already expired")
                score -= 0.3
            if (batch.expiry_date - batch.manufacturing_date).days < 30:
                red_flags.append("Expiry date too soon after manufacturing")
                score -= 0.3
        
        # Check batch quantity consistency
        total_serialized = self.db.query(SerializedUnit).filter(
            SerializedUnit.batch_id == batch_id
        ).count()
        if batch.quantity and total_serialized > batch.quantity * 1.1:
            red_flags.append(f"More units verified than batch quantity ({total_serialized} > {batch.quantity})")
            score -= 0.35
        
        # Check for batch-level counterfeiting patterns
        batch_counterfeits = self.db.query(Verification).filter(
            Verification.batch_id == batch_id,
            Verification.result == "COUNTERFEIT"
        ).count()
        batch_verifications = self.db.query(Verification).filter(
            Verification.batch_id == batch_id
        ).count()
        
        if batch_verifications >= 10:
            batch_counterfeit_rate = batch_counterfeits / batch_verifications
            if batch_counterfeit_rate > 0.1:  # >10% counterfeits in batch
                red_flags.append(f"Batch has high counterfeit rate: {batch_counterfeit_rate:.1%}")
                score -= (batch_counterfeit_rate * 0.5)
        
        return max(0.0, score), red_flags
    
    def analyze_geographic_anomaly(self, serial: str, lat: float, lng: float, 
                                    product_id: int) -> Tuple[float, List[str]]:
        """
        Detect geographic anomalies - products appearing in unexpected locations
        """
        red_flags = []
        score = 0.0  # Start at 0, only increase if checks pass
        
        # Check if location is within Ghana
        if not self._is_within_ghana(lat, lng):
            red_flags.append("Product verified outside Ghana (unexpected)")
            score -= 0.2
        
        # Get previous verifications for this product
        previous_verifications = self.db.query(Verification).filter(
            Verification.serial_number == serial
        ).order_by(Verification.timestamp).all()
        
        if len(previous_verifications) > 0:
            last_location = (
                previous_verifications[-1].location_latitude,
                previous_verifications[-1].location_longitude
            )
            distance_km = self._haversine_distance(last_location, (lat, lng))
            
            # Check for impossibly fast movement
            time_diff = (datetime.utcnow() - previous_verifications[-1].timestamp).total_seconds() / 3600
            
            if time_diff > 0:
                speed_kmh = distance_km / time_diff
                if speed_kmh > 100:  # Faster than typical transport
                    red_flags.append(f"Impossible movement speed: {speed_kmh:.0f} km/h")
                    score -= 0.2
        
        # Check for anomalous distribution pattern
        product_pattern = self.db.query(GeographicAnomalyPattern).filter(
            GeographicAnomalyPattern.product_id == product_id
        ).first()
        
        if product_pattern:
            if lat not in product_pattern.expected_regions:
                red_flags.append(f"Product detected in unexpected region")
                score -= 0.25
            
            # Check if location is in high-risk counterfeiting zone
            for zone in product_pattern.high_risk_zones:
                if self._location_in_zone(lat, lng, zone):
                    red_flags.append(f"Location in known counterfeit hotspot")
                    score -= 0.3
        
        return max(0.0, min(1.0, score)), red_flags
    
    def analyze_time_gap_anomaly(self, serial: str) -> Tuple[float, List[str]]:
        """
        Detect temporal anomalies in verification patterns
        """
        red_flags = []
        score = 1.0
        
        verifications = self.db.query(Verification).filter(
            Verification.serial_number == serial
        ).order_by(Verification.timestamp).all()
        
        if len(verifications) < 2:
            return score, []  # No temporal pattern yet
        
        # Check for unusual time gaps
        gaps_hours = []
        for i in range(len(verifications) - 1):
            gap = (verifications[i + 1].timestamp - verifications[i].timestamp).total_seconds() / 3600
            gaps_hours.append(gap)
        
        # Very short gaps might indicate fraud testing
        short_gaps = [g for g in gaps_hours if 0 < g < 1]
        if len(short_gaps) >= 3:
            red_flags.append(f"Multiple verifications within 1 hour (testing pattern)")
            score -= 0.3
        
        # Very long gaps might indicate old stock
        long_gaps = [g for g in gaps_hours if g > 720]  # >30 days
        if len(long_gaps) > 0:
            red_flags.append(f"Large time gap between verifications (dormant product)")
            score -= 0.15
        
        return score, red_flags
    
    def analyze_verification_pattern(self, serial: str, pharmacy_id: int) -> Tuple[float, List[str]]:
        """
        Analyze verification pattern - who verifies, how often, etc.
        """
        red_flags = []
        score = 1.0
        
        verifications = self.db.query(Verification).filter(
            Verification.serial_number == serial
        ).all()
        
        # Check for repeated verification by same pharmacy
        pharmacy_verify_count = len([v for v in verifications if v.pharmacy_id == pharmacy_id])
        if pharmacy_verify_count > 5:
            red_flags.append(f"Same pharmacy verified this unit {pharmacy_verify_count} times")
            score -= 0.2
        
        # Check result consistency
        results = [v.result for v in verifications]
        if 'COUNTERFEIT' in results and 'AUTHENTIC' in results:
            red_flags.append("Conflicting verification results (authenticated and counterfeit)")
            score -= 0.4
        
        # Check if verified only once (risk flag)
        if len(verifications) == 1:
            score -= 0.1  # Slight reduction for low verification history
        
        return max(0.0, score), red_flags
    
    def calculate_ml_risk_score(self, features: Dict) -> Tuple[float, float]:
        """
        Machine Learning risk scoring
        Simplified model - would use actual ML model in production
        Returns: (risk_score 0-1.0, confidence 0-1.0)
        """
        
        # Feature weights (learned from training data)
        weights = {
            'serial_score': 0.20,
            'batch_score': 0.25,
            'geographic_score': 0.20,
            'time_gap_score': 0.15,
            'pattern_score': 0.10,
            'red_flag_count': 0.10
        }
        
        # Normalize red flag count
        red_flag_score = min(1.0, features.get('red_flag_count', 0) / 5.0)
        
        # Calculate weighted score
        risk_score = (
            features.get('serial_score', 0.5) * weights['serial_score'] +
            features.get('batch_score', 0.5) * weights['batch_score'] +
            features.get('geographic_score', 0.5) * weights['geographic_score'] +
            features.get('time_gap_score', 0.5) * weights['time_gap_score'] +
            features.get('pattern_score', 0.5) * weights['pattern_score'] +
            red_flag_score * weights['red_flag_count']
        )
        
        # Confidence is inversely related to uncertainty
        confidence = 0.75  # Baseline
        if red_flag_score > 0.5:
            confidence += 0.15  # High confidence if many red flags
        if features.get('geographic_score', 0.5) > 0.7:
            confidence += 0.1   # Geographic check adds confidence
        
        return min(1.0, risk_score), min(1.0, confidence)
    
    def detect_fraud(self, request: FraudDetectionRequest) -> FraudDetectionResponse:
        """
        Complete fraud detection analysis
        Main entry point for verification
        """
        
        # Component analysis
        serial_score, serial_flags = self.analyze_serial_number(
            request.serial_number, request.product_id
        )
        
        batch_score, batch_flags = self.analyze_batch_consistency(
            request.batch_number, request.serial_number, request.product_id
        )
        
        geo_score, geo_flags = self.analyze_geographic_anomaly(
            request.serial_number, request.verification_latitude, 
            request.verification_longitude, request.product_id
        )
        
        time_score, time_flags = self.analyze_time_gap_anomaly(request.serial_number)
        
        pattern_score, pattern_flags = self.analyze_verification_pattern(
            request.serial_number, request.pharmacy_id
        )
        
        # Combine all red flags
        all_red_flags = serial_flags + batch_flags + geo_flags + time_flags + pattern_flags
        
        # ML scoring
        features = {
            'serial_score': serial_score,
            'batch_score': batch_score,
            'geographic_score': geo_score,
            'time_gap_score': time_score,
            'pattern_score': pattern_score,
            'red_flag_count': len(all_red_flags)
        }
        
        ml_risk_score, ml_confidence = self.calculate_ml_risk_score(features)
        
        # Determine result
        if ml_risk_score < self.AUTHENTIC_THRESHOLD:
            result = "AUTHENTIC"
            risk_level = FraudRiskLevel.AUTHENTIC
            recommendation = "Accept product"
            suggested_action = "accept"
        elif ml_risk_score < 0.5:
            result = "LIKELY_AUTHENTIC"
            risk_level = FraudRiskLevel.LIKELY_AUTHENTIC
            recommendation = "Likely authentic, proceed with caution"
            suggested_action = "accept"
        elif ml_risk_score < self.COUNTERFEIT_THRESHOLD:
            result = "SUSPICIOUS"
            risk_level = FraudRiskLevel.SUSPICIOUS
            recommendation = "Manually verify or contact manufacturer"
            suggested_action = "verify_manually"
        elif ml_risk_score < 0.85:
            result = "LIKELY_COUNTERFEIT"
            risk_level = FraudRiskLevel.LIKELY_COUNTERFEIT
            recommendation = "Likely counterfeit - escalate to authorities"
            suggested_action = "escalate_to_manufacturer"
        else:
            result = "COUNTERFEIT"
            risk_level = FraudRiskLevel.COUNTERFEIT
            recommendation = "Definitely counterfeit - reject and report"
            suggested_action = "reject"
        
        # Get product fraud history
        product = self.db.query(Product).filter(Product.id == request.product_id).first()
        product_history = self.db.query(ProductFraudHistory).filter(
            ProductFraudHistory.product_id == request.product_id
        ).first()
        
        product_counterfeit_rate = 0.0
        if product_history:
            product_counterfeit_rate = product_history.counterfeit_rate
        
        # Get batch fraud analysis
        batch_analysis = self.db.query(BatchFraudAnalysis).filter(
            BatchFraudAnalysis.batch_id == request.batch_number
        ).first()
        
        batch_counterfeit_rate = 0.0
        if batch_analysis:
            batch_counterfeit_rate = batch_analysis.counterfeit_rate
        
        # Find similar counterfeits
        similar_counterfeits = self.db.query(Verification).filter(
            Verification.product_id == request.product_id,
            Verification.result == "COUNTERFEIT"
        ).count()
        
        return FraudDetectionResponse(
            result=result,
            confidence_score=ml_risk_score,
            risk_level=risk_level,
            risk_factors=features,
            red_flags=all_red_flags,
            batch_consistency_score=batch_score,
            serial_format_score=serial_score,
            geographic_anomaly_score=geo_score,
            time_gap_anomaly_score=time_score,
            verification_pattern_score=pattern_score,
            ml_model_confidence=ml_confidence,
            detection_method="hybrid",  # Combines rules + ML
            recommendation=recommendation,
            suggested_action=suggested_action,
            product_counterfeit_rate=product_counterfeit_rate,
            batch_counterfeit_rate=batch_counterfeit_rate,
            similar_counterfeits_found=similar_counterfeits
        )
    
    # ========== HELPER METHODS ==========
    
    def _is_valid_serial_format(self, serial: str) -> bool:
        """Check if serial follows expected format"""
        # Adjust based on actual serial format requirements
        if len(serial) < 10 or len(serial) > 30:
            return False
        return True
    
    def _is_sequential_serial(self, serial: str) -> bool:
        """Detect if serial is sequential (low entropy)"""
        try:
            if serial.isdigit() and int(serial) % 1000 == 0:
                return True
        except:
            pass
        return False
    
    def _matches_counterfeit_pattern(self, serial: str, product_id: int) -> bool:
        """Check if serial matches known counterfeit patterns"""
        # Query database for known patterns
        return False  # Simplified
    
    def _is_valid_batch_format(self, batch: str) -> bool:
        """Validate batch number format"""
        if len(batch) < 5:
            return False
        return True
    
    def _is_within_ghana(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within Ghana"""
        return (self.GHANA_BOUNDS['south'] <= lat <= self.GHANA_BOUNDS['north'] and
                self.GHANA_BOUNDS['west'] <= lng <= self.GHANA_BOUNDS['east'])
    
    def _haversine_distance(self, point1: Tuple, point2: Tuple) -> float:
        """Calculate distance between two coordinates in km"""
        lat1, lng1 = point1
        lat2, lng2 = point2
        
        R = 6371  # Earth's radius in km
        
        dlat = np.radians(lat2 - lat1)
        dlng = np.radians(lng2 - lng1)
        
        a = (np.sin(dlat/2) ** 2 + 
             np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlng/2) ** 2)
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
    
    def _location_in_zone(self, lat: float, lng: float, zone: Dict) -> bool:
        """Check if location is within a geographic zone"""
        return (zone['south'] <= lat <= zone['north'] and
                zone['west'] <= lng <= zone['east'])


# ============================================================================
# API ENDPOINTS FOR FRAUD DETECTION
# ============================================================================

fraud_router = APIRouter(prefix="/api/v1/fraud", tags=["fraud_detection"])


@fraud_router.post("/detect", response_model=FraudDetectionResponse)
async def detect_fraud(
    request: FraudDetectionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Advanced fraud detection endpoint"""
    
    engine = AdvancedFraudDetectionEngine(db)
    result = engine.detect_fraud(request)
    
    # Save analysis to database
    profile = db.query(SerializedUnitFraudProfile).filter(
        SerializedUnitFraudProfile.unit_id == db.query(SerializedUnit).filter(
            SerializedUnit.serial_number == request.serial_number
        ).first().id
    ).first()
    
    if not profile:
        profile = SerializedUnitFraudProfile(
            unit_id=db.query(SerializedUnit).filter(
                SerializedUnit.serial_number == request.serial_number
            ).first().id,
            product_id=request.product_id,
            batch_id=request.batch_number
        )
        db.add(profile)
    
    profile.current_risk_score = result.confidence_score
    profile.risk_level = result.risk_level
    profile.red_flags = result.red_flags
    profile.ml_features = result.risk_factors
    profile.model_confidence = result.ml_model_confidence
    profile.last_analysis_at = datetime.utcnow()
    
    db.commit()
    
    return result


@fraud_router.get("/patterns/{product_id}", response_model=FraudPatternAnalysis)
async def get_fraud_patterns(
    product_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get fraud patterns for a product (admin only)"""
    
    history = db.query(ProductFraudHistory).filter(
        ProductFraudHistory.product_id == product_id
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="No fraud history for product")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    
    return FraudPatternAnalysis(
        product_id=product_id,
        product_name=product.name,
        counterfeit_rate=history.counterfeit_rate,
        trend=history.counterfeit_trend,
        common_patterns=history.common_red_flags,
        geographic_hotspots=history.high_risk_regions,
        recommended_action="Increase verification requirements"
    )


@fraud_router.get("/batch-analysis/{batch_id}")
async def get_batch_analysis(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """Get fraud analysis for a batch"""
    
    analysis = db.query(BatchFraudAnalysis).filter(
        BatchFraudAnalysis.batch_id == batch_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis for batch")
    
    return {
        "batch_id": batch_id,
        "counterfeit_rate": analysis.counterfeit_rate,
        "risk_level": analysis.batch_risk_level,
        "risk_score": analysis.batch_risk_score,
        "red_flags": analysis.red_flags,
        "distribution_anomalies": analysis.distribution_anomalies
    }
