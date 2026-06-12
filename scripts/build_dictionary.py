import json
import os

# Resoluciones de rutas absolutas para garantizar que el script pueda 
# ejecutarse desde cualquier directorio sin romper los paths relativos.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_DIR = os.path.join(BASE_DIR, "data", "dictionaries")
OUTPUT_FILE = os.path.join(DICT_DIR, "skills_esco.jsonl")

# Semilla de conocimientos tecnológicos
CORE_SKILLS = [
    "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "PHP", "Go", "Swift", "Kotlin",
    "TypeScript", "Rust", "SQL", "NoSQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask", "FastAPI",
    "Spring Boot", "Laravel", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
    "Google Cloud", "Linux", "Git", "CI/CD", "Jenkins", "Terraform", "Ansible",
    "Machine Learning", "Data Science", "Artificial Intelligence", "Deep Learning",
    "NLP", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn",
    "HTML", "CSS", "Tailwind", "Bootstrap", "Sass", "GraphQL", "REST API",
    "Microservices", "Agile", "Scrum", "Kanban"
]

def build_dictionary():
    os.makedirs(DICT_DIR, exist_ok=True)
    print(f"Construyendo diccionario de conocimientos NLP en: {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for skill in CORE_SKILLS:
            # Formateamos estrictamente bajo el estándar JSONL que spaCy requiere para inyectar reglas deterministas en el EntityRuler.
            entry = {
                "label": "SKILL",
                "pattern": skill
            }
            f.write(json.dumps(entry) + "\n")
            
    print(f"Éxito: {len(CORE_SKILLS)} habilidades exportadas y listas para EntityRuler.")

if __name__ == "__main__":
    build_dictionary()