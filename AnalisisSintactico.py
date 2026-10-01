import json
from pathlib import Path


class AnalisisSintactico:
    """Analizador sintactico y semantico del lenguaje de circuitos."""

    def __init__(self, tokens, ruta_reglas=None):
        self.tokens = tokens
        self.pos = 0
        archivo_reglas = Path(ruta_reglas) if ruta_reglas else Path(__file__).with_name("reglas.json")
        try:
            with archivo_reglas.open(encoding="utf-8") as archivo:
                self.especificacion = json.load(archivo)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"No se pudo cargar {archivo_reglas}: {error}") from error

        self.reglas = {regla["nombre"]: regla for regla in self.especificacion["reglas"]}
        if len(self.reglas) != 10:
            raise RuntimeError("reglas.json debe contener exactamente 10 reglas")
        if any(regla["tipo"] != "sintactica" for regla in self.reglas.values()):
            raise RuntimeError("Todas las reglas de reglas.json deben ser sintacticas")
        self.componentes = self.especificacion["componentes"]
        self.configuracion = self.especificacion["configuracion"]

    def actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def regla_activa(self, nombre):
        if nombre not in self.reglas:
            raise RuntimeError(f"La regla {nombre!r} no existe en reglas.json")
        return self.reglas[nombre]

    def componente(self, nombre):
        if nombre not in self.componentes:
            raise RuntimeError(f"El componente {nombre!r} no existe en reglas.json")
        return self.componentes[nombre]

    def es(self, valor):
        token = self.actual()
        return token is not None and str(token.valor).upper() == valor.upper()

    def consumir(self, tipo, valor=None):
        token = self.actual()
        if token is None:
            raise SyntaxError(f"Se esperaba {valor or tipo}, pero se encontro el final del archivo")
        if token.token != tipo or (valor is not None and str(token.valor).upper() != valor.upper()):
            esperado = valor or tipo
            raise SyntaxError(
                f"Se esperaba {esperado}, pero se encontro {token.valor!r} "
                f"(L:{token.linea}, C:{token.columna})"
            )
        self.pos += 1
        return token

    def simbolo(self, nombre):
        return self.consumir("SIMBOLO", self.configuracion["simbolos"][nombre])

    def identificador(self):
        return self.consumir("IDENTIFICADOR").valor

    def lista_identificadores(self):
        self.regla_activa("lista_identificadores")
        nombres = [self.identificador()]
        separador = self.configuracion["simbolos"]["separador"]
        while self.actual() is not None and self.actual().valor == separador:
            self.simbolo("separador")
            nombres.append(self.identificador())
        return nombres

    def revisarSintaxis(self):
        return self.analizar()

    def analizar(self):
        self.regla_activa("programa")
        self.regla_activa("declaraciones")
        self.consumir("PALABRA_RESERVADA", self.configuracion["inicio"])
        nombre = self.identificador()
        self.simbolo("apertura_programa")
        declaraciones = []
        while self.actual() is not None and not self.es(self.configuracion["fin"]):
            if self.actual().valor == self.configuracion["simbolos"]["cierre_programa"]:
                break
            declaraciones.append(self.declaracion())
        self.simbolo("cierre_programa")
        self.consumir("PALABRA_RESERVADA", self.configuracion["fin"])
        if self.actual() is not None and self.actual().valor == self.configuracion["simbolos"]["fin_declaracion"]:
            self.simbolo("fin_declaracion")
        self.consumir("EOF")
        self.validar_semantica(declaraciones)
        return {"tipo": "CIRCUITO", "nombre": nombre, "declaraciones": declaraciones}

    def validar_semantica(self, declaraciones):
        validaciones = self.configuracion["validaciones_semanticas"]
        declarados = set()
        for declaracion in declaraciones:
            nombres = []
            if declaracion["tipo"] in ("ENTRADA", "SALIDA"):
                nombres = declaracion["nombres"]
            elif declaracion["tipo"] == "CONSTANTE":
                nombres = [declaracion["nombre"]]
            for nombre in nombres:
                if nombre in declarados and validaciones.get("identificadores_unicos", False):
                    raise SyntaxError(f"Identificador declarado mas de una vez: {nombre!r}")
                declarados.add(nombre)

        if validaciones.get("referencias_declaradas", False):
            for declaracion in declaraciones:
                if declaracion["tipo"] == "CONECTAR":
                    referencias = declaracion["origen"] + [declaracion["destino"]]
                elif declaracion["tipo"] == "SIMULAR":
                    referencias = [valor for valor in declaracion["entradas"] if isinstance(valor, str)]
                else:
                    continue
                for referencia in referencias:
                    if referencia.upper() in self.configuracion["booleanos"]:
                        continue
                    if referencia not in declarados:
                        raise SyntaxError(f"Identificador no declarado: {referencia!r}")

        destinos = {
            declaracion["destino"]
            for declaracion in declaraciones
            if declaracion["tipo"] == "CONECTAR"
        }
        if validaciones.get("salidas_conectadas", False):
            for declaracion in declaraciones:
                if declaracion["tipo"] == "SALIDA":
                    for salida in declaracion["nombres"]:
                        if salida not in destinos:
                            raise SyntaxError(f"La salida no esta conectada: {salida!r}")

        entradas = sum(
            len(declaracion["nombres"])
            for declaracion in declaraciones
            if declaracion["tipo"] == "ENTRADA"
        )
        if validaciones.get("simulacion_valida", False):
            for declaracion in declaraciones:
                if declaracion["tipo"] == "SIMULAR" and len(declaracion["entradas"]) != entradas:
                    raise SyntaxError(
                        "SIMULAR debe recibir un valor por cada entrada "
                        f"(se esperaban {entradas}, se recibieron {len(declaracion['entradas'])})"
                    )

        for declaracion in declaraciones:
            if declaracion["tipo"] != "CONECTAR":
                continue
            compuerta = declaracion["compuerta"]
            cantidad = len(declaracion["origen"])
            if compuerta == "NOT" and cantidad != 1:
                raise SyntaxError("La compuerta NOT necesita exactamente una entrada")
            if compuerta != "NOT" and cantidad != 2:
                raise SyntaxError(f"La compuerta {compuerta} necesita exactamente dos entradas")

    def declaracion(self):
        self.regla_activa("declaracion")
        tipo = str(self.actual().valor).upper()
        if tipo not in self.configuracion["declaraciones"]:
            token = self.actual()
            raise SyntaxError(f"Declaracion no reconocida: {token.valor!r} (L:{token.linea}, C:{token.columna})")

        if tipo in ("ENTRADA", "SALIDA"):
            self.regla_activa("declaracion_entrada_salida")
            self.consumir("PALABRA_RESERVADA", tipo)
            nombres = self.lista_identificadores()
            self.simbolo("fin_declaracion")
            return {"tipo": tipo, "nombres": nombres}

        if tipo == "CONSTANTE":
            self.regla_activa("declaracion_constante")
            self.consumir("PALABRA_RESERVADA", tipo)
            nombre = self.identificador()
            self.consumir("OPERADOR", self.configuracion["operadores"]["asignacion"])
            valor = self.booleano()
            self.simbolo("fin_declaracion")
            return {"tipo": tipo, "nombre": nombre, "valor": valor == "VERDADERO"}

        if tipo == "CONECTAR":
            self.regla_activa("declaracion_conectar")
            self.consumir("PALABRA_RESERVADA", tipo)
            compuerta = self.configuracion["operadores"]["compuerta_predeterminada"]
            if self.actual() is not None and self.actual().valor.upper() in self.configuracion["compuertas"]:
                compuerta = self.compuerta()
            origen = self.lista_identificadores()
            self.consumir("FLECHA", self.configuracion["operadores"]["conexion"])
            destino = self.identificador()
            self.simbolo("fin_declaracion")
            return {"tipo": tipo, "compuerta": compuerta, "origen": origen, "destino": destino}

        if tipo == "SIMULAR":
            self.regla_activa("declaracion_simular")
            self.consumir("PALABRA_RESERVADA", tipo)
            entradas = self.lista_valores()
            self.simbolo("fin_declaracion")
            return {"tipo": tipo, "entradas": entradas}

        self.regla_activa("declaracion_tabla_verdad")
        self.consumir("PALABRA_RESERVADA", "TABLA_DE_VERDAD")
        self.simbolo("fin_declaracion")
        return {"tipo": "TABLA_DE_VERDAD"}

    def booleano(self):
        self.componente("booleano")
        token = self.consumir("PALABRA_RESERVADA")
        valor = token.valor.upper()
        if valor not in self.configuracion["booleanos"]:
            raise SyntaxError("Se esperaba VERDADERO o FALSO")
        return valor

    def compuerta(self):
        self.componente("compuerta")
        token = self.consumir("PALABRA_RESERVADA")
        valor = token.valor.upper()
        if valor not in self.configuracion["compuertas"]:
            raise SyntaxError(f"Compuerta no valida: {valor}")
        return valor

    def lista_valores(self):
        self.regla_activa("lista_valores")
        self.componente("valor")
        valores = []
        if self.actual() is not None and self.actual().valor == self.configuracion["simbolos"]["apertura_lista"]:
            self.simbolo("apertura_lista")
            valores.append(self.valor())
            while self.actual() is not None and self.actual().valor == self.configuracion["simbolos"]["separador"]:
                self.simbolo("separador")
                valores.append(self.valor())
            self.simbolo("cierre_lista")
        else:
            valores = self.lista_identificadores()
        return valores

    def valor(self):
        self.componente("valor")
        token = self.actual()
        if token.token == "NUMERO":
            return float(self.consumir("NUMERO").valor)
        if token.token == "IDENTIFICADOR":
            return self.consumir("IDENTIFICADOR").valor
        if token.token == "PALABRA_RESERVADA" and token.valor.upper() in self.configuracion["booleanos"]:
            return self.booleano()
        raise SyntaxError(f"Valor no valido: {token.valor!r}")

    def simular_circuito(self, circuito):
        """Calcula las salidas del circuito para la declaracion SIMULAR."""
        declaraciones = circuito["declaraciones"]
        entradas = [
            nombre
            for declaracion in declaraciones
            if declaracion["tipo"] == "ENTRADA"
            for nombre in declaracion["nombres"]
        ]
        simulaciones = [
            declaracion["entradas"]
            for declaracion in declaraciones
            if declaracion["tipo"] == "SIMULAR"
        ]
        valores_simulados = simulaciones[-1] if simulaciones else []
        valores = {}
        for declaracion in declaraciones:
            if declaracion["tipo"] == "CONSTANTE":
                valores[declaracion["nombre"]] = declaracion["valor"]
        valores.update(
            zip(entradas, (self._valor_logico(valor, valores) for valor in valores_simulados))
        )

        for declaracion in declaraciones:
            if declaracion["tipo"] != "CONECTAR":
                continue
            origen = [valores[nombre] for nombre in declaracion["origen"]]
            valores[declaracion["destino"]] = self._calcular_compuerta(
                declaracion["compuerta"], origen
            )

        salidas = [
            nombre
            for declaracion in declaraciones
            if declaracion["tipo"] == "SALIDA"
            for nombre in declaracion["nombres"]
        ]
        return {salida: valores.get(salida) for salida in salidas}

    @staticmethod
    def _valor_logico(valor, valores):
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, (int, float)):
            if valor not in (0, 1, 0.0, 1.0):
                raise SyntaxError("Los valores numericos deben ser 0 o 1")
            return bool(valor)
        if isinstance(valor, str) and valor.upper() in ("VERDADERO", "FALSO"):
            return valor.upper() == "VERDADERO"
        if valor in valores:
            return valores[valor]
        raise SyntaxError(f"No se pudo convertir a booleano: {valor!r}")

    @staticmethod
    def _calcular_compuerta(compuerta, valores):
        if compuerta == "AND":
            return valores[0] and valores[1]
        if compuerta == "OR":
            return valores[0] or valores[1]
        if compuerta == "NOT":
            return not valores[0]
        if compuerta == "XOR":
            return valores[0] != valores[1]
        if compuerta == "NAND":
            return not (valores[0] and valores[1])
        if compuerta == "NOR":
            return not (valores[0] or valores[1])
        if compuerta == "XNOR":
            return valores[0] == valores[1]
        raise SyntaxError(f"Compuerta no implementada: {compuerta}")


AnalizadorSintactico = AnalisisSintactico
