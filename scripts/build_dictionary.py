import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_DIR = os.path.join(BASE_DIR, "data", "dictionaries")
OUTPUT_FILE = os.path.join(DICT_DIR, "skills_esco.jsonl")

CORE_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Ruby",
    "PHP", "Go", "Rust", "Swift", "Kotlin",
    "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask",
    "FastAPI", "Spring Boot", ".NET",
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "SQLite", "NoSQL", "Redis",
    "Cassandra", "Elasticsearch",
    "AWS", "Azure", "Google Cloud", "GCP", "Docker", "Kubernetes",
    "Terraform", "Jenkins", "CI/CD", "Linux",
    "Machine Learning", "Data Science", "Artificial Intelligence", "NLP",
    "Deep Learning", "TensorFlow", "PyTorch", "Pandas", "NumPy",
    "Scikit-learn",
    "Git", "GitHub", "GitLab", "Bitbucket",
    "Agile", "Scrum", "Jira", "Figma",
    "HTML", "CSS", "Sass", "Tailwind", "Bootstrap",
    "GraphQL", "REST API", "Microservices",
]


def build_dictionary():
    os.makedirs(DICT_DIR, exist_ok=True)
    print(f"Construyendo diccionario NLP en: {OUTPUT_FILE}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for skill in CORE_SKILLS:
            # Formateamos bajo el estandar JSONL que spaCy requiere para
            # inyectar reglas deterministicas en el EntityRuler.
            entry = {"label": "SKILL", "pattern": skill}
            f.write(json.dumps(entry) + "\n")

    print(f"Exito: {len(CORE_SKILLS)} habilidades exportadas.")


if __name__ == "__main__":
    build_dictionary()