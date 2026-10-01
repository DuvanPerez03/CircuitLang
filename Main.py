import shlex
import sys
from pathlib import Path

from AnalisisLexico import AnalisisLexico
from AnalisisSintactico import AnalisisSintactico


def leer_archivo(ruta_archivo):
    if not ruta_archivo.lower().endswith(".cir"):
        print(f"Tipo de archivo no valido: '{ruta_archivo}'. Usa un archivo con extension .cir.")
        return None
    try:
        with open(ruta_archivo, encoding="utf-8") as archivo:
            return archivo.read()
    except OSError as error:
        print(f"No se pudo leer el archivo '{ruta_archivo}': {error}")
        return None


def rutas_posibles(ruta_archivo):
    ruta = Path(ruta_archivo)
    if ruta.is_absolute():
        return [ruta]

    bases = [
        Path.cwd(),
        Path(sys.executable).resolve().parent,
        Path(sys.executable).resolve().parent.parent,
    ]
    return list(dict.fromkeys(base / ruta for base in bases))


def ejecutar():
    if len(sys.argv) > 1:
        texto = leer_archivo(sys.argv[1])
        if texto is None:
            return
    else:
        print("Escribe el nombre o la ruta de un archivo .cir, o introduce el circuito completo y termina con FIN;.")
        primera_linea = input().strip()
        candidatos = [primera_linea.strip('"')]
        partes_comando = shlex.split(primera_linea, posix=False)
        if partes_comando:
            candidatos.append(partes_comando[-1].strip('"'))

        texto = None
        for ruta_archivo in candidatos:
            if not ruta_archivo.lower().endswith(".cir"):
                continue
            for ruta_posible in rutas_posibles(ruta_archivo):
                if ruta_posible.is_file():
                    texto = leer_archivo(str(ruta_posible))
                    break
            if texto is not None:
                break

        if texto is None:
            if any(ruta.lower().endswith(".cir") for ruta in candidatos):
                print(f"No se encontro el archivo .cir indicado: '{candidatos[-1]}'")
                return
            if candidatos and Path(candidatos[-1]).suffix:
                leer_archivo(candidatos[-1])
                return
            print("Escribe el circuito. Finaliza con FIN;")
            lineas = [primera_linea]
            while True:
                linea = input()
                lineas.append(linea)
                if linea.strip().upper().endswith("FIN;"):
                    break

            texto = "\n".join(lineas)

    tokens = AnalisisLexico(texto).analizar()

    print("\n=== TOKENS ===")
    print(tokens)

    analizador = AnalisisSintactico(tokens)
    resultado = analizador.revisarSintaxis()

    print("\n=== PROGRAMA VALIDADO ===")
    print(f"Circuito: {resultado['nombre']}")
    print("Declaraciones:")
    for declaracion in resultado["declaraciones"]:
        if declaracion["tipo"] == "CONECTAR":
            origen = ", ".join(declaracion["origen"])
            print(f"  - Compuerta {declaracion['compuerta']}: {origen} -> {declaracion['destino']}")
        elif declaracion["tipo"] in ("ENTRADA", "SALIDA"):
            nombres = ", ".join(declaracion["nombres"])
            print(f"  - {declaracion['tipo'].capitalize()}: {nombres}")
        elif declaracion["tipo"] == "CONSTANTE":
            valor = str(declaracion["valor"]).upper()
            print(f"  - Constante: {declaracion['nombre']} = {valor}")
        else:
            nombre = declaracion["tipo"].replace("_", " ").capitalize()
            print(f"  - {nombre}")

    print("\n=== RESULTADO DE LA SIMULACION ===")
    salidas = analizador.simular_circuito(resultado)
    for nombre, valor in salidas.items():
        print(f"  {nombre} = {str(valor).upper()}")

    print("\nResultado completo:", resultado)


if __name__ == "__main__":
    try:
        ejecutar()
    except (EOFError, KeyboardInterrupt):
        print("\nEjecucion cancelada por el usuario.")
    except Exception as error:
        print("\n=== ERROR ===")
        print(f"{type(error).__name__}: {error}")
        print("El programa no pudo procesar el circuito. Revisa la entrada y reglas.json.")
    finally:
        if len(sys.argv) == 1:
            try:
                input("\nPresiona Enter para cerrar...")
            except EOFError:
                pass
