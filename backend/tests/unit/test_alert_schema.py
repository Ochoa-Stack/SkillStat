import pytest
from marshmallow import ValidationError
from app.schemas.alert_schema import AlertRequestSchema


def test_absolute_alert_valid_payload():
    schema = AlertRequestSchema()
    payload = {
        "skill_id": 1,
        "alert_type": "ABSOLUTE",
        "threshold_value": 100
    }
    result = schema.load(payload)
    assert result["skill_id"] == 1
    assert result["alert_type"] == "ABSOLUTE"
    assert result["threshold_value"] == 100
    assert "threshold_percentage" not in result


def test_absolute_alert_missing_threshold_value():
    schema = AlertRequestSchema()
    payload = {
        "skill_id": 1,
        "alert_type": "ABSOLUTE"
    }
    with pytest.raises(ValidationError) as exc:
        schema.load(payload)
    assert "threshold_value" in exc.value.messages


def test_absolute_alert_rejects_threshold_percentage():
    schema = AlertRequestSchema()
    payload = {
        "skill_id": 1,
        "alert_type": "ABSOLUTE",
        "threshold_value": 100,
        "threshold_percentage": 10.5
    }
    with pytest.raises(ValidationError) as exc:
        schema.load(payload)
    assert "threshold_percentage" in exc.value.messages


def test_trend_alert_valid_payload():
    schema = AlertRequestSchema()
    payload = {
        "skill_id": 1,
        "alert_type": "TREND",
        "threshold_percentage": 15.5
    }
    result = schema.load(payload)
    assert result["skill_id"] == 1
    assert result["alert_type"] == "TREND"
    assert "threshold_value" not in result
    # It might cast to Decimal, so we just check it's present and correct
    assert float(result["threshold_percentage"]) == 15.5


def test_trend_alert_missing_threshold_percentage():
    schema = AlertRequestSchema()
    payload = {
        "skill_id": 1,
        "alert_type": "TREND"
    }
    with pytest.raises(ValidationError) as exc:
        schema.load(payload)
    assert "threshold_percentage" in exc.value.messages


def test_trend_alert_rejects_threshold_value():
    schema = AlertRequestSchema()
    payload = {
        "skill_id": 1,
        "alert_type": "TREND",
        "threshold_percentage": 15.5,
        "threshold_value": 100
    }
    with pytest.raises(ValidationError) as exc:
        schema.load(payload)
    assert "threshold_value" in exc.value.messages


def test_invalid_alert_type_rejected():
    schema = AlertRequestSchema()
    payload = {
        "skill_id": 1,
        "alert_type": "INVALID",
        "threshold_value": 100
    }
    with pytest.raises(ValidationError) as exc:
        schema.load(payload)
    assert "alert_type" in exc.value.messages


def test_threshold_value_must_be_positive():
    schema = AlertRequestSchema()
    payload_zero = {
        "skill_id": 1,
        "alert_type": "ABSOLUTE",
        "threshold_value": 0
    }
    with pytest.raises(ValidationError) as exc:
        schema.load(payload_zero)
    assert "threshold_value" in exc.value.messages

    payload_negative = {
        "skill_id": 1,
        "alert_type": "ABSOLUTE",
        "threshold_value": -5
    }
    with pytest.raises(ValidationError) as exc:
        schema.load(payload_negative)
    assert "threshold_value" in exc.value.messages


def test_threshold_percentage_must_be_positive():
    schema = AlertRequestSchema()
    payload_zero = {
        "skill_id": 1,
        "alert_type": "TREND",
        "threshold_percentage": 0
    }
    with pytest.raises(ValidationError) as exc:
        schema.load(payload_zero)
    assert "threshold_percentage" in exc.value.messages

    payload_negative = {
        "skill_id": 1,
        "alert_type": "TREND",
        "threshold_percentage": -5.5
    }
    with pytest.raises(ValidationError) as exc:
        schema.load(payload_negative)
    assert "threshold_percentage" in exc.value.messages
