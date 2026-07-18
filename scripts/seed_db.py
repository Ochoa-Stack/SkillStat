from app import create_app
from app.extensions import db
from app.models.skill import Skill

SEED_SKILLS = [
    {"name": "Python", "canonical_name": "PYTHON", "category_id": 1},
    {"name": "React", "canonical_name": "REACT", "category_id": 2},
    {"name": "Vue", "canonical_name": "VUE", "category_id": 2},
    {"name": "Flask", "canonical_name": "FLASK", "category_id": 3},
    {"name": "Django", "canonical_name": "DJANGO", "category_id": 3},
    {"name": "Docker", "canonical_name": "DOCKER", "category_id": 4},
    {"name": "AWS", "canonical_name": "AWS", "category_id": 4},
    {"name": "PostgreSQL", "canonical_name": "POSTGRESQL", "category_id": 5},
    {"name": "Pandas", "canonical_name": "PANDAS", "category_id": 5},
    {"name": "Microservicios", "canonical_name": "MICROSERVICIOS", "category_id": 6},
]

def seed_skills():
    app = create_app()
    with app.app_context():
        for skill_data in SEED_SKILLS:
            existing = db.session.execute(
                db.select(Skill).filter_by(name=skill_data["name"])
            ).scalar_one_or_none()
            if existing:
                print(f"Skill ya existe, se omite: {skill_data['name']}")
                continue
            skill = Skill(**skill_data)
            db.session.add(skill)
        db.session.commit()
        print(f"Seed completado: {len(SEED_SKILLS)} skills verificados/creados.")

if __name__ == "__main__":
    seed_skills()