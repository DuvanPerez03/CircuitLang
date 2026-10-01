import re

from Token import Token

class AnalisisLexico:
    def __init__(self, texto):
        self.texto = texto
        self.tokens = []
        self.i = 0
        self.linea = 1
        self.columna = 1
        self.palabras_reservadas = {
            "CIRCUITO", "FIN", "ENTRADA", "SALIDA", "CONSTANTE",
            "CONECTAR", "SIMULAR", "TABLA_DE_VERDAD", "SUBCIRCUITO",
            "FIN_SUBCIRCUITO", "USAR", "AND", "OR", "NOT", "XOR",
            "NAND", "NOR", "XNOR", "VERDADERO", "FALSO"
        }
        self.RE_IDENTIFICADOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
        self.RE_NUMERO = re.compile(r"[0-9]+(?:\.[0-9]+)?")
        self.RE_CADENA = re.compile(r'"(?:\\.|[^"\\])*"')
        self.RE_ESPACIOS = re.compile(r"\s+")

        self.REGLAS = [
            ("COMENTARIO", re.compile(r"//[^\n]*|\#[^\n]*")),
            ("NUMERO", self.RE_NUMERO),
            ("CADENA", self.RE_CADENA),
            ("IDENTIFICADOR", self.RE_IDENTIFICADOR),
            ("FLECHA", re.compile(r"->")),
            ("OPERADOR", re.compile(r"==|!=|<=|>=|&&|\|\||[=!]")),
            ("SIMBOLO", re.compile(r"[(),;{}.:]")),
        ]

    def avanzar(self, lexema):
        """Actualiza la posicion del lexer despues de consumir un lexema."""
        saltos = lexema.count("\n")
        if saltos:
            self.linea += saltos
            self.columna = len(lexema.rsplit("\n", 1)[1]) + 1
        else:
            self.columna += len(lexema)
        self.i += len(lexema)

    def analizar(self):
        while self.i < len(self.texto):
            espacios = self.RE_ESPACIOS.match(self.texto, self.i)
            if espacios:
                self.avanzar(espacios.group())
                continue

            inicio_linea, inicio_columna = self.linea, self.columna
            encontrado = False
            for tipo, patron in self.REGLAS:
                coincidencia = patron.match(self.texto, self.i)
                if not coincidencia:
                    continue

                lexema = coincidencia.group()
                self.avanzar(lexema)
                encontrado = True

                if tipo == "COMENTARIO":
                    break
                if tipo == "IDENTIFICADOR" and lexema.upper() in self.palabras_reservadas:
                    tipo = "PALABRA_RESERVADA"
                elif tipo == "IDENTIFICADOR":
                    tipo = "IDENTIFICADOR"
                elif tipo == "NUMERO":
                    tipo = "NUMERO"
                self.tokens.append(Token(tipo, lexema, inicio_linea, inicio_columna))
                break

            if not encontrado:
                caracter = self.texto[self.i]
                raise ValueError(
                    f"Caracter no reconocido: {caracter!r} "
                    f"en L:{inicio_linea}, C:{inicio_columna}"
                )

        self.tokens.append(Token("EOF", None, self.linea, self.columna))
        return self.tokens

