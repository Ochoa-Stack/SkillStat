import pytest
from datetime import datetime, timezone, timedelta

from app.models.city import City
from app.models.category import Category
from app.models.skill import Skill
from app.models.trend_snapshot import TrendSnapshot
from app.repositories.skill_repository import SkillRepository
from app.repositories.trend_snapshot_repository import TrendSnapshotRepository

# Helpers
def _make_city(db_session, city_id=2, name="City"):
    city = City(id=city_id, name=name, state="State", country="MX")
    db_session.add(city)
    db_session.flush()
    return city

def _make_category(db_session, name="Category"):
    cat = Category(name=name)
    db_session.add(cat)
    db_session.flush()
    return cat

def _make_skill(db_session, category_id, name="Skill"):
    skill = Skill(name=name, canonical_name=name.upper(), category_id=category_id)
    db_session.add(skill)
    db_session.flush()
    return skill

def _make_snapshot(db_session, skill_id, city_id, demand_count=10, days_ago=0):
    snap_date = datetime.now(timezone.utc).date() - timedelta(days=days_ago)
    snap = TrendSnapshot(
        skill_id=skill_id,
        city_id=city_id,
        date=snap_date,
        demand_count=demand_count,
        growth_rate=None,
        avg_salary=None,
    )
    db_session.add(snap)
    db_session.commit()
    return snap

def test_skill_get_by_ids_returns_matching_skills_only(app, db_session):
    cat = _make_category(db_session)
    s1 = _make_skill(db_session, cat.id, name="S1")
    s2 = _make_skill(db_session, cat.id, name="S2")
    s3 = _make_skill(db_session, cat.id, name="S3")
    
    with app.app_context():
        skills = SkillRepository.get_by_ids([s1.id, s3.id])
        assert len(skills) == 2
        ids = {s.id for s in skills}
        assert s1.id in ids
        assert s3.id in ids
        assert s2.id not in ids

def test_trend_snapshot_get_by_skill_ids_returns_all_snapshots_for_given_skills(app, db_session):
    cat = _make_category(db_session)
    city = _make_city(db_session)
    s1 = _make_skill(db_session, cat.id, name="SnapS1")
    s2 = _make_skill(db_session, cat.id, name="SnapS2")
    
    _make_snapshot(db_session, s1.id, city.id, days_ago=1)
    _make_snapshot(db_session, s1.id, city.id, days_ago=2)
    _make_snapshot(db_session, s2.id, city.id, days_ago=3)
    _make_snapshot(db_session, s2.id, city.id, days_ago=4)
    
    with app.app_context():
        snaps = TrendSnapshotRepository.get_by_skill_ids([s1.id, s2.id])
        assert len(snaps) == 4

def test_trend_snapshot_get_latest_by_skill_ids_returns_one_per_skill(app, db_session):
    cat = _make_category(db_session)
    city = _make_city(db_session, city_id=99)
    s1 = _make_skill(db_session, cat.id, name="LatestS1")
    s2 = _make_skill(db_session, cat.id, name="LatestS2")
    
    # 3 snapshots per skill, days_ago ensures different dates (1 is most recent)
    s1_snap1 = _make_snapshot(db_session, s1.id, city.id, days_ago=1)
    s1_snap2 = _make_snapshot(db_session, s1.id, city.id, days_ago=2)
    s1_snap3 = _make_snapshot(db_session, s1.id, city.id, days_ago=3)
    
    s2_snap1 = _make_snapshot(db_session, s2.id, city.id, days_ago=5)
    s2_snap2 = _make_snapshot(db_session, s2.id, city.id, days_ago=10)
    s2_snap3 = _make_snapshot(db_session, s2.id, city.id, days_ago=15)
    
    with app.app_context():
        snaps = TrendSnapshotRepository.get_latest_by_skill_ids([s1.id, s2.id])
        assert len(snaps) == 2
        
        # Verify exactly one snapshot per skill id and it's the most recent one
        s1_returned = next(s for s in snaps if s.skill_id == s1.id)
        s2_returned = next(s for s in snaps if s.skill_id == s2.id)
        
        assert s1_returned.date == s1_snap1.date
        assert s2_returned.date == s2_snap1.date

def test_trend_snapshot_get_latest_by_skill_ids_empty_list_returns_empty(app, db_session):
    with app.app_context():
        snaps = TrendSnapshotRepository.get_latest_by_skill_ids([])
        assert isinstance(snaps, list)
        assert len(snaps) == 0
