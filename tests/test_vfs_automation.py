#!/usr/bin/env python3
"""
Test script for VFS automation functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.vfs_automation import VFSAutomation, AvailabilityStatus
from services.csv_io import ClientRecord

def test_availability_check():
    """Test availability checking functionality."""
    print("Testing VFS availability check...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    try:
        if automation.start_browser():
            print("✅ Browser started successfully")
            
            # Test availability check (short duration for testing)
            availability = automation.check_availability(duration_minutes=1)
            
            print(f"Availability Status:")
            print(f"  Available: {availability.available}")
            print(f"  Slots: {availability.slots_count}")
            print(f"  Last Checked: {availability.last_checked}")
            if availability.error_message:
                print(f"  Error: {availability.error_message}")
                
        else:
            print("❌ Failed to start browser")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
    finally:
        automation.stop_browser()
        print("Browser stopped")

def test_client_booking():
    """Test booking with sample client data."""
    print("\nTesting client booking...")
    
    # Create sample client
    sample_client = ClientRecord(
        first_name="John",
        last_name="Doe",
        date_of_birth="01/01/1990",
        email="john.doe@example.com",
        password="password123",
        mobile_country_code="245",
        mobile_number="123456789",
        passport_number="A12345678",
        visa_type="Tourist Visa",
        application_center="Bissau",
        service_center="Standard Service",
        trip_reason="Tourism",
        gender="Male",
        current_nationality="Guinea-Bissau",
        passport_expiry="01/01/2030"
    )
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    try:
        if automation.start_browser():
            print("✅ Browser started for booking test")
            
            # Test booking (this will likely fail due to no real availability)
            result = automation.book_appointment(sample_client)
            
            print(f"Booking Result:")
            print(f"  Success: {result.success}")
            print(f"  Booking Reference: {result.booking_reference}")
            print(f"  Error: {result.error_message}")
            print(f"  Client: {result.client_email}")
            print(f"  Timestamp: {result.timestamp}")
            
        else:
            print("❌ Failed to start browser for booking test")
            
    except Exception as e:
        print(f"❌ Booking test failed: {str(e)}")
    finally:
        automation.stop_browser()
        print("Browser stopped for booking test")

if __name__ == "__main__":
    print("VFS Automation Test Suite")
    print("=" * 50)
    
    # Test availability checking
    test_availability_check()
    
    # Test client booking
    test_client_booking()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
