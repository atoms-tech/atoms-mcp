#!/usr/bin/env python3
"""
Verification script for dashboard and alerting extraction.

Run this to verify all modules are properly extracted and working.
"""

import sys
import asyncio
from datetime import datetime


def test_imports():
    """Test that all modules can be imported."""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)
    
    try:
        # Dashboard imports
        from observability.dashboards import (
            MetricAggregator,
            DashboardDataCollector,
            DashboardFormatter,
            MetricType,
        )
        print("✓ Dashboard modules imported successfully")
        
        # Alerting imports
        from observability.alerting import (
            AlertManager,
            AlertSeverity,
            Alert,
            AlertState,
            AlertRule,
            ThresholdCondition,
            RateCondition,
        )
        print("✓ Alerting modules imported successfully")
        
        # Optional WebSocket
        try:
            from observability.dashboards import WebSocketDashboard
            print("✓ WebSocket support available")
        except ImportError:
            print("ℹ WebSocket support not available (install websockets)")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


async def test_dashboard():
    """Test dashboard functionality."""
    print("\n" + "=" * 60)
    print("TESTING DASHBOARD")
    print("=" * 60)
    
    try:
        from observability.dashboards import (
            MetricAggregator,
            DashboardDataCollector,
            DashboardFormatter,
            MetricType,
        )
        
        # Create aggregator
        aggregator = MetricAggregator()
        
        # Record some metrics
        await aggregator.record_metric("test_counter", 1, MetricType.COUNTER)
        await aggregator.record_metric("test_gauge", 0.75, MetricType.GAUGE)
        
        # Get metrics
        metrics = await aggregator.get_metrics(time_range_minutes=5)
        print(f"✓ Recorded and retrieved {len(metrics)} metrics")
        
        # Create collector
        collector = DashboardDataCollector(metric_aggregator=aggregator)
        
        # Get dashboard data
        data = await collector.get_dashboard_data()
        print(f"✓ Dashboard data collected: {len(data)} fields")
        
        # Test formatter
        formatter = DashboardFormatter()
        status = formatter.format_component_status(
            "test_component",
            "healthy",
            response_time_ms=42.5,
            last_check=datetime.now(),
        )
        print(f"✓ Formatted component status: {status['name']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Dashboard test failed: {e}")
        return False


async def test_alerting():
    """Test alerting functionality."""
    print("\n" + "=" * 60)
    print("TESTING ALERTING")
    print("=" * 60)
    
    try:
        from observability.alerting import (
            AlertManager,
            AlertSeverity,
            AlertRule,
            ThresholdCondition,
        )
        
        # Create manager
        manager = AlertManager()
        
        # Register alert
        alert = manager.register_alert(
            name="test_alert",
            description="Test alert",
            severity=AlertSeverity.HIGH,
            condition="value > 10",
            threshold=10.0,
        )
        print(f"✓ Registered alert: {alert.name}")
        
        # Create rule
        rule = AlertRule(
            name="cpu_rule",
            description="CPU high",
            severity=AlertSeverity.HIGH,
            condition=ThresholdCondition("cpu_usage", 0.9, ">"),
            threshold=0.9,
        )
        
        # Evaluate rule
        result = rule.evaluate({"cpu_usage": 0.95})
        print(f"✓ Alert rule evaluation: {result}")
        
        # Trigger alert
        alert.state = "resolved"  # Reset first
        manager.trigger_alert(alert.alert_id, current_value=15.0)
        print(f"✓ Triggered alert: {alert.is_active}")
        
        # Get active alerts
        active = manager.get_active_alerts()
        print(f"✓ Active alerts: {len(active)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Alerting test failed: {e}")
        return False


async def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("DASHBOARD & ALERTING EXTRACTION VERIFICATION")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test imports
    results.append(test_imports())
    
    # Test dashboard
    results.append(await test_dashboard())
    
    # Test alerting
    results.append(await test_alerting())
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if all(results):
        print("\n✓ All verification tests passed!")
        print("\nExtraction successful! All modules are working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
