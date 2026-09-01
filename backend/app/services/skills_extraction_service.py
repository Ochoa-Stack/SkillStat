import os
import json
import spacy
from app.utils.errors import AppError

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)
DICT_PATH = os.path.join(BASE_DIR, "data", "dictionaries", "skills_esco.jsonl")

# Carga del modelo NLP a nivel de módulo. 
# Esto garantiza que el impacto en CPU/RAM ocurra solo una vez al arrancar la aplicación y no en cada llamada al servicio durante el procesamiento de vacantes.
try:
    nlp = spacy.load(
        "es_core_news_sm",
        disable=["ner", "parser", "tagger", "lemmatizer", "attribute_ruler"],
    )

    if not os.path.exists(DICT_PATH):
        raise FileNotFoundError(f"Diccionario no encontrado en: {DICT_PATH}")

    # Forzamos que el EntityRuler opere antes del componente ner y con overwrite_ents=True para que sus matches tengan prioridad absoluta sobre cualquier entidad que otros componentes del pipeline produzcan.
    ruler = nlp.add_pipe(
        "entity_ruler",
        before="ner",
        config={"overwrite_ents": True},
    )

    patterns = []
    with open(DICT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                patterns.append(json.loads(line))

    ruler.add_patterns(patterns)
    nlp_error = None

except Exception as e:
    nlp = None
    nlp_error = str(e)


class SkillsExtractionService:
    # Capa de dominio puro. Recibe texto, devuelve entidades de conocimiento.
    
    @classmethod
    def extract_skills(cls, text: str) -> list:
        if not nlp:
            raise AppError(f"El motor NLP falló en su inicialización: {nlp_error}", code="NLP_INIT_ERROR")
            
        if not text or not isinstance(text, str):
            return []
            
        # Procesamos el texto crudo contra las reglas inyectadas
        doc = nlp(text)
        
        # Filtramos entidades etiquetadas como SKILL. Utilizamos un set para erradicar duplicados si una vacante menciona "Python" varias veces.
        skills_found = {ent.text for ent in doc.ents if ent.label_ == "SKILL"}
        
        return list(skills_found)
