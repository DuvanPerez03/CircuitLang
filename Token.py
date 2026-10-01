class Token:
    def __init__(self, token, valor, linea=1, columna=1):
        self.token = token
        self.valor = valor
        self.linea = linea
        self.columna = columna

    def to_json(self):
        return self.__dict__

    def __repr__(self):
        return f"({self.token} - {self.valor!r} [L:{self.linea}, C:{self.columna}])"