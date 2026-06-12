import os
import spacy
from app.utils.errors import AppError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_PATH = os.path.join(BASE_DIR, "data", "dictionaries", "skills_esco.jsonl")

# Carga del modelo NLP a nivel de módulo. 
# Esto garantiza que el impacto en CPU/RAM ocurra solo una vez al arrancar la aplicación y no en cada llamada al servicio durante el procesamiento de vacantes.
try:
    # Desactivamos los componentes pesados (ner, parser, tagger) que no usamos para acelerar masivamente el procesamiento de las descripciones.
    nlp = spacy.load("es_core_news_sm", disable=["ner", "parser", "tagger", "lemmatizer", "attribute_ruler"])
    
    if not os.path.exists(DICT_PATH):
        raise FileNotFoundError(f"Diccionario no encontrado en: {DICT_PATH}")
        
    # Inyectamos nuestro propio EntityRuler con los datos extraídos de ESCO
    ruler = nlp.add_pipe("entity_ruler")
    ruler.from_disk(DICT_PATH)
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
        
        # Filtramos entidades etiquetadas como SKILL.
        # Utilizamos un set para erradicar duplicados si una vacante menciona "Python" varias veces.
        skills_found = {ent.text for ent in doc.ents if ent.label_ == "SKILL"}
        
        return list(skills_found)
