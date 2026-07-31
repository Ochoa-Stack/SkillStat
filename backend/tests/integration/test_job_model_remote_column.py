import pytest
from app.models.job import Job

def test_job_remote_defaults_to_false_when_not_specified(app, db_session):
    """ crea un Job sin especificar remote, lo persiste, lo recupera con una query nueva y afirma que remote es False """
    job = Job(
        source="Test Source",
        title="Test Job Title",
        raw_description="This is a test job description",
        description_hash="hash1234567890abcdef"
    )
    db_session.add(job)
    db_session.commit()
    
    db_session.expire_all()
    
    with app.app_context():
        fetched_job = db_session.get(Job, job.id)
        assert fetched_job is not None
        assert fetched_job.remote is False

def test_job_remote_persists_explicit_true_value(app, db_session):
    """ crea un Job con remote=True explícito, lo persiste, lo recupera igual que el test anterior, y afirma que remote es True """
    job = Job(
        source="Test Source 2",
        title="Test Job Title 2",
        raw_description="This is another test job description",
        description_hash="hash0987654321fedcba",
        remote=True
    )
    db_session.add(job)
    db_session.commit()
    
    db_session.expire_all()
    
    with app.app_context():
        fetched_job = db_session.get(Job, job.id)
        assert fetched_job is not None
        assert fetched_job.remote is True
