import os
import sys
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ConfigurationError
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class CloudDatabaseManager:
    _database_instance = None

    @classmethod
    def get_connection(cls):
        if cls._database_instance is not None:
            return cls._database_instance
        # Si experimenta problemas de ruta con el .env en su laptop, puede inyectar su URI directo aquí temporalmente:
        uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "TU_CADENA_DE_CONEXION_DE_ATLAS_AQUÍ"
        db_name = os.getenv("DB_NAME", "game_cloud")
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000, tls=True)
            client.admin.command('ping')
            cls._database_instance = client[db_name]
            return cls._database_instance
        except Exception as e:
            print(f"❌ Error de infraestructura: {e}")
            raise


# =====================================================================
# BLANCOS DE IMPLEMENTACIÓN (A resolver por el alumno)
# =====================================================================

def desplegar_coleccion_con_gobernanza(db):
    """
    IMPLEMENTACIÓN BLOQUE 1 Y BLOQUE 2 (80 PUNTOS)
    Construye la sintaxis completa del comando administrativo db.create_collection()
    aplicando las reglas de JSON Schema detalladas en la hoja de instrucciones.
    """
    
    # 1. Definir el esquema estructural de validación NoSQL
    esquema_validador = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["isbn", "titulo", "caracteres_totales", "precio"],
            "properties": {
                "isbn": {
                    "bsonType": "string",
                    "pattern": "^ISBN-[0-9]{13}$",
                    "description": "Debe ser un string que cumpla con el patrón '^ISBN-[0-9]{13}$' y es obligatorio"
                },
                "titulo": {
                    "bsonType": "string",
                    "description": "Debe ser un string y es obligatorio"
                },
                "caracteres_totales": {
                    "bsonType": "int",
                    "description": "Debe ser un entero de 32 bits (int) y es obligatorio"
                },
                "precio": {
                    "bsonType": "double",
                    "minimum": 0.01,
                    "description": "Debe ser un número flotante (double) mayor o igual a 0.01 y es obligatorio"
                }
            }
        }
    }
    
    try:
        # Eliminamos la colección previa para limpiar el laboratorio del maestro
        if "libros_validados" in db.list_collection_names():
            db["libros_validados"].drop()
            
        print("📥 [Gobernanza]: Desplegando reglas perimetrales de JSON Schema en Atlas...")
        
        # 2. Crear la colección inyectando las restricciones y la acción de error
        db.create_collection(
            "libros_validados",
            validator=esquema_validador,
            validationAction="error"  # <-- Fuerza al clúster cloud a abortar transacciones corruptas
        )
        print("✅ [Éxito]: Muralla estructural JSON Schema activa de forma perimetral.")
        
    except Exception as e:
        print(f"❌ Error al configurar el validador: {e}")
        raise


def ejecutar_pruebas_gobernanza(db):
    """
    Pruebas operativas para validar la gobernanza perimetral:
    1. Inserción de documentos válidos (incluyendo atributos elásticos adicionales).
    2. Rechazo de documentos inválidos (tipos erróneos, rangos negativos, regex ISBN no coincidentes, campos ausentes).
    """
    coleccion = db["libros_validados"]
    print("\n" + "="*70)
    print("🧪 INICIANDO PRUEBAS DE GOBERNANZA DE DATOS (E-CHURCH INTEGRITY)")
    print("="*70)

    # 1. Prueba de Documento Válido
    doc_valido = {
        "isbn": "ISBN-9788491162506",
        "titulo": "Biblia de Estudio Teológico",
        "caracteres_totales": 1250000,
        "precio": 350.50,
        "editorial": "Editorial Eclesiástica", # Campo adicional para demostrar flexibilidad elástica
        "idioma": "Español"
    }

    try:
        resultado = coleccion.insert_one(doc_valido)
        print(f"✅ Inserción válida exitosa. _id generado: {resultado.inserted_id}")
    except OperationFailure as e:
        print(f"❌ Fallo inesperado en documento válido: {e}")

    # 2. Casos de Prueba Inválidos
    casos_invalidos = [
        {
            "descripcion": "Falta el campo obligatorio 'precio'",
            "doc": {
                "isbn": "ISBN-9788491162506",
                "titulo": "Libro sin precio",
                "caracteres_totales": 50000
            }
        },
        {
            "descripcion": "Precio con valor menor al mínimo permitido (precio: -5.00)",
            "doc": {
                "isbn": "ISBN-9788491162506",
                "titulo": "Libro con precio negativo",
                "caracteres_totales": 50000,
                "precio": -5.0
            }
        },
        {
            "descripcion": "Precio igual a 0.0 (mínimo es 0.01)",
            "doc": {
                "isbn": "ISBN-9788491162506",
                "titulo": "Libro con precio cero",
                "caracteres_totales": 50000,
                "precio": 0.0
            }
        },
        {
            "descripcion": "Formato de ISBN inválido (no coincide con '^ISBN-[0-9]{13}$')",
            "doc": {
                "isbn": "9788491162506",  # Falta el prefijo ISBN-
                "titulo": "Libro sin prefijo ISBN",
                "caracteres_totales": 50000,
                "precio": 99.99
            }
        },
        {
            "descripcion": "Longitud de ISBN inválida ('ISBN-123')",
            "doc": {
                "isbn": "ISBN-123",
                "titulo": "Libro con ISBN corto",
                "caracteres_totales": 50000,
                "precio": 99.99
            }
        },
        {
            "descripcion": "Tipo de dato incorrecto en 'caracteres_totales' (string en vez de int)",
            "doc": {
                "isbn": "ISBN-9788491162506",
                "titulo": "Libro con caracteres string",
                "caracteres_totales": "50000",
                "precio": 99.99
            }
        },
        {
            "descripcion": "Tipo de dato incorrecto en 'precio' (int en vez de double)",
            "doc": {
                "isbn": "ISBN-9788491162506",
                "titulo": "Libro con precio entero",
                "caracteres_totales": 50000,
                "precio": 100  # En BSON es int32, debe ser double
            }
        }
    ]

    print("\n--- Ejecutando pruebas de rechazo (Muralla Perimetral) ---")
    for caso in casos_invalidos:
        try:
            coleccion.insert_one(caso["doc"])
            print(f"❌ ERROR: Se permitió insertar documento corrupto: {caso['descripcion']}")
        except OperationFailure as err:
            print(f"🛡️ RECHAZADO CORRECTAMENTE (validationAction='error'): {caso['descripcion']}")

    print("="*70 + "\n")


if __name__ == "__main__":
    db = CloudDatabaseManager.get_connection()
    desplegar_coleccion_con_gobernanza(db)
    ejecutar_pruebas_gobernanza(db)
