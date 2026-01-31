#!/usr/bin/env python3
"""
Phase 1 Test: Simulation Foundation
Tests the hospital simulator, data generator, and busy_thursday scenario.
"""
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.simulation.hospital_sim import HospitalSimulator
from backend.simulation.scenarios.busy_thursday import BusyThursdayScenario
from backend.simulation.event_types import (
    PatientArrivalSimEvent,
    VitalsUpdateSimEvent,
    LabResultSimEvent,
    DeteriorationSimEvent
)


class Phase1Tester:
    """Test Phase 1 simulation components"""
    
    def __init__(self):
        self.events = []
        self.arrivals = 0
        self.vitals_updates = 0
        self.lab_results = 0
        self.deteriorations = 0
    
    async def event_handler(self, event):
        """Handle simulation events"""
        self.events.append(event)
        
        if isinstance(event, PatientArrivalSimEvent):
            self.arrivals += 1
            print(f"\n[{event.sim_time:6.1f} min] 🚑 ARRIVAL: Patient {event.patient_id}")
            print(f"    Severity: {event.severity.value}")
            print(f"    Complaint: {event.chief_complaint}")
            print(f"    Mode: {event.arrival_mode.value}")
            if event.deterioration_pattern.value != "stable":
                print(f"    ⚠️  Deterioration pattern: {event.deterioration_pattern.value}")
        
        elif isinstance(event, VitalsUpdateSimEvent):
            self.vitals_updates += 1
            if event.deterioration_indicator:
                print(f"[{event.sim_time:6.1f} min] 📊 VITALS: Patient {event.patient_id}")
                print(f"    HR: {event.heart_rate} | BP: {event.blood_pressure_systolic}/{event.blood_pressure_diastolic}")
                print(f"    SpO2: {event.oxygen_saturation}% | RR: {event.respiratory_rate} | GCS: {event.glasgow_coma_scale}")
                print(f"    ⚠️  Pattern: {event.deterioration_indicator}")
        
        elif isinstance(event, LabResultSimEvent):
            self.lab_results += 1
            if event.critical:
                print(f"[{event.sim_time:6.1f} min] 🧪 LAB (CRITICAL): Patient {event.patient_id}")
                print(f"    {event.test_name}: {event.value} {event.unit} (normal: {event.normal_range_low}-{event.normal_range_high})")
        
        elif isinstance(event, DeteriorationSimEvent):
            self.deteriorations += 1
            print(f"[{event.sim_time:6.1f} min] 🚨 DETERIORATION: Patient {event.patient_id}")
            print(f"    Type: {event.deterioration_type.value}")
            print(f"    Change: {event.severity_change}")
            print(f"    Escalation needed: {event.needs_escalation}")
    
    def print_summary(self, simulator):
        """Print test summary"""
        print("\n" + "="*70)
        print("PHASE 1 TEST SUMMARY")
        print("="*70)
        
        print(f"\n📊 Event Statistics:")
        print(f"   Patient Arrivals: {self.arrivals}")
        print(f"   Vitals Updates: {self.vitals_updates}")
        print(f"   Lab Results: {self.lab_results}")
        print(f"   Deterioration Events: {self.deteriorations}")
        print(f"   Total Events: {len(self.events)}")
        
        patients = simulator.get_current_patients()
        print(f"\n👥 Patient Statistics:")
        print(f"   Total Patients: {len(patients)}")
        
        # Count by severity (from chief complaints)
        critical = sum(1 for p in patients if "sepsis" in p.chief_complaint.lower() or "respiratory failure" in p.chief_complaint.lower())
        high = sum(1 for p in patients if any(x in p.chief_complaint.lower() for x in ["chest pain", "stroke", "trauma"]))
        
        print(f"   Critical: ~{critical}")
        print(f"   High Severity: ~{high}")
        print(f"   Other: {len(patients) - critical - high}")
        
        # Check deteriorating patients
        deteriorating = [p for p in patients if any(e.patient_id == p.id for e in self.events if isinstance(e, DeteriorationSimEvent))]
        print(f"   Deteriorating: {len(deteriorating)}")
        
        print(f"\n⏱  Simulation Time: {simulator.get_simulation_time():.1f} minutes")
        
        print("\n" + "="*70)
        
        # Validation
        print("\n✅ VALIDATION:")
        checks = [
            (self.arrivals >= 15, f"Expected 15 arrivals, got {self.arrivals}"),
            (self.vitals_updates > 0, f"Expected vitals updates, got {self.vitals_updates}"),
            (self.deteriorations >= 2, f"Expected 2+ deteriorations, got {self.deteriorations}"),
            (len(patients) >= 15, f"Expected 15 patients, got {len(patients)}")
        ]
        
        all_passed = True
        for passed, message in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status}: {message}")
            if not passed:
                all_passed = False
        
        return all_passed


async def test_phase1():
    """Run Phase 1 tests"""
    print("="*70)
    print(" PHASE 1 TEST: Simulation Foundation")
    print("="*70)
    print("\nTesting: Hospital Simulator + Busy Thursday Scenario")
    print("Expected: 15 patients, 2 deteriorating, 2 hours simulation\n")
    
    # Create tester
    tester = Phase1Tester()
    
    # Create simulator with event callback
    simulator = HospitalSimulator(
        event_callback=tester.event_handler,
        time_scale=1.0
    )
    
    # Load scenario
    print("📋 Loading Busy Thursday scenario...\n")
    BusyThursdayScenario.setup(simulator)
    
    # Run simulation
    print("🏃‍♂️ Running simulation (120 minutes simulated time)...\n")
    await simulator.run_async(until=120)
    
    # Print results
    success = tester.print_summary(simulator)
    
    if success:
        print("\n🎉 Phase 1 PASSED! Simulation foundation is working correctly.")
        return 0
    else:
        print("\n❌ Phase 1 FAILED! Please check the issues above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_phase1())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
