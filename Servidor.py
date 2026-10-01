from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from AnalisisLexico import AnalisisLexico
from AnalisisSintactico import AnalizadorSintactico

app = FastAPI(
    title="Circuito DSL API",
    description="API para procesar y simular circuitos del lenguaje .cir",
    version="1.0"
)

class CodigoRequest(BaseModel):
    codigo: str = Field(
        ...,
        description="Codigo completo de un circuito en formato .cir",
        examples=["""CIRCUITO demo {
ENTRADA a, b;
SALIDA resultado;
CONECTAR AND a, b -> resultado;
SIMULAR (VERDADERO, FALSO);
} FIN;"""],
    )

@app.get("/")
def inicio():
    return FileResponse("index.html")


@app.get("/api/estado")
def estado():
    return {"lenguaje": "Circuito", "version": "v1.0", "estado": "En ejecucion"}

@app.post("/iniciar")
def ejecutar_codigo(request: CodigoRequest):
    try:
        codigo = request.codigo.strip()
        if not codigo:
            return {"error": "No se ingreso codigo"}
        
        # Analisis Lexico
        lexico = AnalisisLexico(codigo)
        tokens = lexico.analizar()
        
        # Analisis Sintactico
        sintactico = AnalizadorSintactico(tokens)
        ast = sintactico.analizar()
        
        return {
            "exito": True,
            "ast": ast,
            "simulacion": sintactico.simular_circuito(ast),
            "tokens": [
                {
                    "tipo": t.token,
                    "valor": t.valor, 
                    "linea": t.linea, 
                    "columna": t.columna
                } for t in tokens
            ]
        }
    except SyntaxError as error:
        return {"error": f"Error de sintaxis: {str(error)}"}
    except Exception as error:
        return {"error": f"Error interno: {str(error)}"}