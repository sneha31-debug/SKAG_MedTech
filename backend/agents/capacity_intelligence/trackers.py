"""
Capacity Intelligence Agent - Tracking Logic

Real-time tracking for hospital beds and staff, with availability prediction.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from .models import (
    BedStatus, BedState, StaffWorkload, UnitCapacity, 
    UnitType, CapacityAssessment
)


class BedTracker:
    """
    Tracks bed status changes and calculates occupancy metrics.
    
    Maintains an in-memory view of all beds across hospital units.
    In production, this would sync with a database/state manager.
    """
    
    def __init__(self):
        self._beds: Dict[str, BedStatus] = {}
        self._beds_by_unit: Dict[UnitType, List[str]] = defaultdict(list)
    
    def register_bed(self, bed: BedStatus) -> None:
        """Register a new bed in the tracking system."""
        self._beds[bed.bed_id] = bed
        if bed.bed_id not in self._beds_by_unit[bed.unit]:
            self._beds_by_unit[bed.unit].append(bed.bed_id)
    
    def update_bed_state(
        self, 
        bed_id: str, 
        new_state: BedState, 
        patient_id: Optional[str] = None,
        estimated_available_at: Optional[datetime] = None
    ) -> Optional[BedStatus]:
        """Update the state of a bed."""
        if bed_id not in self._beds:
            return None
        
        bed = self._beds[bed_id]
        bed.state = new_state
        bed.patient_id = patient_id if new_state == BedState.OCCUPIED else None
        bed.last_state_change = datetime.now()
        bed.estimated_available_at = estimated_available_at
        
        return bed
    
    def get_bed(self, bed_id: str) -> Optional[BedStatus]:
        """Get a specific bed's status."""
        return self._beds.get(bed_id)
    
    def get_unit_beds(self, unit: UnitType) -> List[BedStatus]:
        """Get all beds for a specific unit."""
        bed_ids = self._beds_by_unit.get(unit, [])
        return [self._beds[bid] for bid in bed_ids if bid in self._beds]
    
    def get_unit_capacity(self, unit: UnitType) -> UnitCapacity:
        """Calculate current capacity metrics for a unit."""
        beds = self.get_unit_beds(unit)
        
        total = len(beds)
        occupied = sum(1 for b in beds if b.state == BedState.OCCUPIED)
        available = sum(1 for b in beds if b.state == BedState.AVAILABLE)
        reserved = sum(1 for b in beds if b.state == BedState.RESERVED)
        cleaning = sum(1 for b in beds if b.state == BedState.CLEANING)
        
        return UnitCapacity(
            unit=unit,
            total_beds=total,
            occupied_beds=occupied,
            available_beds=available,
            reserved_beds=reserved,
            cleaning_beds=cleaning
        )
    
    def get_available_beds(self, unit: Optional[UnitType] = None) -> List[BedStatus]:
        """Get all available beds, optionally filtered by unit."""
        if unit:
            beds = self.get_unit_beds(unit)
        else:
            beds = list(self._beds.values())
        
        return [b for b in beds if b.is_available]
    
    def get_all_units_capacity(self) -> Dict[UnitType, UnitCapacity]:
        """Get capacity metrics for all tracked units."""
        capacities = {}
        for unit in self._beds_by_unit.keys():
            capacities[unit] = self.get_unit_capacity(unit)
        return capacities


class StaffTracker:
    """
    Tracks staff assignments and workload.
    
    Monitors staff-to-patient ratios and identifies capacity constraints.
    """
    
    def __init__(self):
        self._staff: Dict[str, StaffWorkload] = {}
        self._staff_by_unit: Dict[UnitType, List[str]] = defaultdict(list)
    
    def register_staff(self, staff: StaffWorkload) -> None:
        """Register a staff member in the tracking system."""
        self._staff[staff.staff_id] = staff
        if staff.staff_id not in self._staff_by_unit[staff.unit]:
            self._staff_by_unit[staff.unit].append(staff.staff_id)
    
    def assign_patient(self, staff_id: str, patient_id: str) -> bool:
        """Assign a patient to a staff member."""
        if staff_id not in self._staff:
            return False
        
        staff = self._staff[staff_id]
        if patient_id not in staff.assigned_patients:
            staff.assigned_patients.append(patient_id)
            staff.current_patient_count = len(staff.assigned_patients)
        return True
    
    def unassign_patient(self, staff_id: str, patient_id: str) -> bool:
        """Remove a patient from a staff member's assignment."""
        if staff_id not in self._staff:
            return False
        
        staff = self._staff[staff_id]
        if patient_id in staff.assigned_patients:
            staff.assigned_patients.remove(patient_id)
            staff.current_patient_count = len(staff.assigned_patients)
        return True
    
    def get_staff(self, staff_id: str) -> Optional[StaffWorkload]:
        """Get a staff member's workload."""
        return self._staff.get(staff_id)
    
    def get_unit_staff(self, unit: UnitType) -> List[StaffWorkload]:
        """Get all staff for a specific unit."""
        staff_ids = self._staff_by_unit.get(unit, [])
        return [self._staff[sid] for sid in staff_ids if sid in self._staff]
    
    def get_unit_staff_metrics(self, unit: UnitType) -> Dict:
        """Get aggregate staff metrics for a unit."""
        staff = self.get_unit_staff(unit)
        
        if not staff:
            return {
                "staff_count": 0,
                "total_capacity": 0,
                "current_load": 0,
                "available_capacity": 0,
                "average_workload": 0.0
            }
        
        total_capacity = sum(s.max_patient_capacity for s in staff)
        current_load = sum(s.current_patient_count for s in staff)
        available_capacity = sum(s.available_capacity for s in staff)
        avg_workload = sum(s.workload_ratio for s in staff) / len(staff)
        
        return {
            "staff_count": len(staff),
            "total_capacity": total_capacity,
            "current_load": current_load,
            "available_capacity": available_capacity,
            "average_workload": avg_workload
        }
    
    def find_available_staff(self, unit: UnitType, min_capacity: int = 1) -> List[StaffWorkload]:
        """Find staff with available capacity in a unit."""
        staff = self.get_unit_staff(unit)
        return [s for s in staff if s.available_capacity >= min_capacity]
    
    def get_least_loaded_staff(self, unit: UnitType) -> Optional[StaffWorkload]:
        """Find the staff member with the lowest workload in a unit."""
        staff = self.get_unit_staff(unit)
        if not staff:
            return None
        return min(staff, key=lambda s: s.workload_ratio)


class AvailabilityPredictor:
    """
    Predicts when beds will become available.
    
    Uses historical data and current state to estimate future availability.
    """
    
    # Average times for state transitions (in minutes)
    DEFAULT_CLEANING_TIME = 30
    DEFAULT_DISCHARGE_PREP_TIME = 60
    
    # Average length of stay by unit type (in hours)
    AVG_LOS = {
        UnitType.ICU: 72,
        UnitType.WARD: 96,
        UnitType.ED: 4,
        UnitType.OR: 3,
        UnitType.PACU: 2
    }
    
    def __init__(self, bed_tracker: BedTracker):
        self.bed_tracker = bed_tracker
    
    def predict_next_available(self, unit: UnitType) -> Optional[datetime]:
        """
        Predict when the next bed will become available in a unit.
        
        Checks:
        1. Beds in cleaning state (shortest wait)
        2. Beds with estimated availability times
        3. Historical discharge patterns
        """
        beds = self.bed_tracker.get_unit_beds(unit)
        now = datetime.now()
        
        # Check for beds already in transition
        cleaning_beds = [b for b in beds if b.state == BedState.CLEANING]
        if cleaning_beds:
            # Estimate based on when cleaning started
            earliest = min(
                b.last_state_change + timedelta(minutes=self.DEFAULT_CLEANING_TIME)
                for b in cleaning_beds
            )
            return max(earliest, now)
        
        # Check beds with estimated availability
        with_estimates = [
            b for b in beds 
            if b.estimated_available_at and b.estimated_available_at > now
        ]
        if with_estimates:
            return min(b.estimated_available_at for b in with_estimates)
        
        # Fall back to average LOS prediction
        occupied_beds = [b for b in beds if b.state == BedState.OCCUPIED]
        if occupied_beds:
            avg_los_hours = self.AVG_LOS.get(unit, 48)
            # Assume some beds are near discharge
            estimated = now + timedelta(hours=avg_los_hours * 0.1)  # 10% of avg LOS
            return estimated
        
        return None
    
    def predict_availability_in_timeframe(
        self, 
        unit: UnitType, 
        timeframe_minutes: int = 60
    ) -> Tuple[int, float]:
        """
        Predict how many beds will become available within a timeframe.
        
        Returns:
            Tuple of (predicted_count, confidence)
        """
        beds = self.bed_tracker.get_unit_beds(unit)
        now = datetime.now()
        cutoff = now + timedelta(minutes=timeframe_minutes)
        
        predicted = 0
        confidence = 0.9
        
        # Count beds in cleaning (high confidence)
        cleaning_beds = [
            b for b in beds 
            if b.state == BedState.CLEANING 
            and b.last_state_change + timedelta(minutes=self.DEFAULT_CLEANING_TIME) <= cutoff
        ]
        predicted += len(cleaning_beds)
        
        # Count beds with explicit estimated availability
        with_estimates = [
            b for b in beds 
            if b.estimated_available_at 
            and now < b.estimated_available_at <= cutoff
        ]
        predicted += len(with_estimates)
        
        # Add probabilistic estimate for occupied beds (lower confidence)
        occupied = sum(1 for b in beds if b.state == BedState.OCCUPIED)
        if occupied > 0:
            avg_los_hours = self.AVG_LOS.get(unit, 48)
            # Probability of discharge in timeframe
            discharge_prob = timeframe_minutes / (avg_los_hours * 60)
            expected_discharges = occupied * min(discharge_prob, 0.3)  # Cap at 30%
            predicted += int(expected_discharges)
            confidence *= 0.7  # Lower confidence for probabilistic predictions
        
        return predicted, confidence


class CapacityTrackingSystem:
    """
    Unified tracking system combining bed and staff tracking with predictions.
    
    This is the main interface used by the Capacity Intelligence Agent.
    """
    
    def __init__(self):
        self.bed_tracker = BedTracker()
        self.staff_tracker = StaffTracker()
        self.predictor = AvailabilityPredictor(self.bed_tracker)
    
    def get_unit_assessment(self, unit: UnitType) -> CapacityAssessment:
        """
        Generate a complete capacity assessment for a unit.
        
        This is the primary output method for the Capacity Intelligence Agent.
        """
        # Get bed capacity
        unit_capacity = self.bed_tracker.get_unit_capacity(unit)
        
        # Add staff information
        staff_metrics = self.staff_tracker.get_unit_staff_metrics(unit)
        unit_capacity.staff_on_duty = staff_metrics["staff_count"]
        
        # Predict availability
        predicted = self.predictor.predict_next_available(unit)
        
        # Generate assessment
        return CapacityAssessment.from_unit_capacity(unit_capacity, predicted)
    
    def get_all_assessments(self) -> Dict[str, CapacityAssessment]:
        """Get capacity assessments for all tracked units."""
        assessments = {}
        for unit in UnitType:
            assessment = self.get_unit_assessment(unit)
            assessments[unit.value] = assessment
        return assessments
    
    def initialize_demo_data(self):
        """Initialize with demo hospital data for testing."""
        # ICU: 10 beds, 80% occupied
        for i in range(10):
            bed = BedStatus(
                bed_id=f"ICU-{i+1:02d}",
                unit=UnitType.ICU,
                state=BedState.OCCUPIED if i < 8 else BedState.AVAILABLE,
                patient_id=f"P-ICU-{i+1}" if i < 8 else None
            )
            self.bed_tracker.register_bed(bed)
        
        # Ward: 30 beds, 70% occupied
        for i in range(30):
            state = BedState.OCCUPIED if i < 21 else BedState.AVAILABLE
            if i == 21:
                state = BedState.CLEANING  # One bed being cleaned
            bed = BedStatus(
                bed_id=f"WARD-{i+1:02d}",
                unit=UnitType.WARD,
                state=state,
                patient_id=f"P-WARD-{i+1}" if i < 21 else None
            )
            self.bed_tracker.register_bed(bed)
        
        # ED: 15 beds, 90% occupied
        for i in range(15):
            bed = BedStatus(
                bed_id=f"ED-{i+1:02d}",
                unit=UnitType.ED,
                state=BedState.OCCUPIED if i < 14 else BedState.AVAILABLE,
                patient_id=f"P-ED-{i+1}" if i < 14 else None
            )
            self.bed_tracker.register_bed(bed)
        
        # Add some staff
        for i in range(3):
            staff = StaffWorkload(
                staff_id=f"ICU-RN-{i+1}",
                name=f"ICU Nurse {i+1}",
                role="nurse",
                unit=UnitType.ICU,
                current_patient_count=3 if i < 2 else 2,
                max_patient_capacity=4
            )
            self.staff_tracker.register_staff(staff)
        
        for i in range(8):
            staff = StaffWorkload(
                staff_id=f"WARD-RN-{i+1}",
                name=f"Ward Nurse {i+1}",
                role="nurse",
                unit=UnitType.WARD,
                current_patient_count=3 if i < 5 else 2,
                max_patient_capacity=5
            )
            self.staff_tracker.register_staff(staff)
        
        for i in range(5):
            staff = StaffWorkload(
                staff_id=f"ED-RN-{i+1}",
                name=f"ED Nurse {i+1}",
                role="nurse",
                unit=UnitType.ED,
                current_patient_count=3,
                max_patient_capacity=4
            )
            self.staff_tracker.register_staff(staff)
