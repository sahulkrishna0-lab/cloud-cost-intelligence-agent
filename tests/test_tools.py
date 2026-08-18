"""
Simple tests for Cloud Cost Intelligence Agent tools.
Tests the mock-data tools to verify they return correct structure.
"""

import pytest
from src.tools import (
    get_cost_data,
    get_instance_utilization,
    get_ri_recommendations,
    check_idle_resources,
)


def test_get_cost_data_returns_total():
    """Cost data should have a positive total."""
    result = get_cost_data.invoke({
        "account_id": "123456789012",
        "days": 30,
        "granularity": "DAILY",
    })
    assert result["total_cost"] > 0
    assert result["currency"] == "USD"


def test_get_cost_data_service_breakdown():
    """Should include service-level breakdown."""
    result = get_cost_data.invoke({
        "account_id": "123456789012",
        "days": 30,
        "granularity": "DAILY",
    })
    assert len(result["service_breakdown"]) > 0


def test_get_cost_data_daily_costs_count():
    """Daily costs length should match requested days."""
    result = get_cost_data.invoke({
        "account_id": "123456789012",
        "days": 14,
        "granularity": "DAILY",
    })
    assert len(result["daily_costs"]) == 14


def test_instance_utilization_categories():
    """Should categorize instances."""
    result = get_instance_utilization.invoke({
        "account_id": "123456789012",
        "days": 30,
    })
    assert "underutilized_instances" in result
    assert "optimal_instances" in result
    assert "overutilized_instances" in result


def test_instance_utilization_underutilized_cpu():
    """Underutilized instances should have CPU < 20%."""
    result = get_instance_utilization.invoke({
        "account_id": "123456789012",
        "days": 30,
    })
    for inst in result["underutilized_instances"]:
        assert inst["avg_cpu_percent"] < 20


def test_ri_recommendations_has_savings():
    """Should provide recommendations with savings."""
    result = get_ri_recommendations.invoke({
        "account_id": "123456789012",
        "lookback_days": 30,
    })
    assert len(result["recommendations"]) > 0
    for rec in result["recommendations"]:
        assert rec["estimated_monthly_savings"] > 0


def test_idle_resources_found():
    """Should find idle resources."""
    result = check_idle_resources.invoke({"account_id": "123456789012"})
    assert len(result["idle_resources"]) > 0


def test_idle_resources_types():
    """Should detect multiple resource types."""
    result = check_idle_resources.invoke({"account_id": "123456789012"})
    types = {r["resource_type"] for r in result["idle_resources"]}
    assert "EBS Volume" in types
    assert len(types) >= 3
