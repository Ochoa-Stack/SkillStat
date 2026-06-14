import json
import os

def build_tech_dictionary():
    # Resolución de ruta absoluta para garantizar ejecución desde cualquier directorio
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dict_dir = os.path.join(base_dir, "data", "dictionaries")
    os.makedirs(dict_dir, exist_ok=True)
    
    output_file = os.path.join(dict_dir, "skills_esco.jsonl")

    # Línea base de habilidades tecnológicas (Sustituto inicial y focalizado de la taxonomía cruda)
    core_skills = [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Ruby", "PHP", "Go", "Rust", "Swift", "Kotlin",
        "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring Boot", ".NET",
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "SQLite", "NoSQL", "Redis", "Cassandra", "Elasticsearch",
        "AWS", "Azure", "Google Cloud", "GCP", "Docker", "Kubernetes", "Terraform", "Jenkins", "CI/CD", "Linux",
        "Machine Learning", "Data Science", "Artificial Intelligence", "NLP", "Deep Learning", "TensorFlow", "PyTorch", "Pandas", "NumPy",
        "Git", "GitHub", "GitLab", "Bitbucket", "Agile", "Scrum", "Jira", "Figma", "HTML", "CSS", "Sass", "Tailwind"
    ]

    print(f"Construyendo diccionario NLP con {len(core_skills)} habilidades base...")

    with open(output_file, "w", encoding="utf-8") as f:
        for skill in core_skills:
            # spaCy EntityRuler format: {"label": "ENT_TYPE", "pattern": "exact_string_or_list"}
            entry = {"label": "SKILL", "pattern": skill}
            f.write(json.dumps(entry) + "\n")

    print(f"Diccionario generado exitosamente en: {output_file}")

if __name__ == "__main__":
    build_tech_dictionary()
