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

    patterns = []
    for skill in CORE_SKILLS:
        # Agregamos el patrón original y su variante en minúsculas para que el EntityRuler capture la habilidad sin importar cómo la escriba la bolsa de trabajo en la descripción de la vacante.
        patterns.append({"label": "SKILL", "pattern": skill})
        if skill != skill.lower():
            patterns.append({"label": "SKILL", "pattern": skill.lower()})

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in patterns:
            f.write(json.dumps(entry) + "\n")

    print(f"Exito: {len(CORE_SKILLS)} habilidades base → {len(patterns)} patrones exportados.")


if __name__ == "__main__":
    build_dictionary()
