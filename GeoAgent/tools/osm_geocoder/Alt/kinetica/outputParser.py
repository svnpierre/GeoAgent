from langchain_community.chat_models.kinetica import KineticaSqlResponse
from langchain_core.output_parsers.transform import BaseOutputParser
import re
from typing import Any, List
from langchain_core.output_parsers.transform import BaseOutputParser
from langchain_core.outputs import Generation
from langchain_core.pydantic_v1 import Field

class KineticaCustomSqlOutputParser(BaseOutputParser[KineticaSqlResponse]):
    """Fetch and return data from the Kinetica LLM.

    This object is used as the last element of a chain to execute generated SQL."""

    kdbc: Any = Field(exclude=True)
    """ Kinetica DB connection. """

    class Config:
        arbitrary_types_allowed = True

    def parse(self, text: str) -> KineticaSqlResponse: 
        # SQLs aufspalten. Zwei Fälle: SQL-String mit einem Statement bzw. mehreren Unterstatements --> Direkt ausführbar, SQL-String bestehend aus mehreren getrennten Statements (z.B. erst Geocoding dann Abfrage) --> Getrennte Ausführung nötig
        statements = [part.strip() for part in re.split(r';(?=(?:[^\'"]*[\'"][^\'"]*[\'"])*[^\'"]*$)', text.strip()) if part.strip()]
        # Alle Statements vor dem letzten Statement ausführen
        for statement in statements[:-1]:
            try:
                self.kdbc.execute_sql(statement)  
            except Exception as e:
                return str(e)           
        # Nur das letzte Statement als DataFrame zurückliefern
        try:
            df = self.kdbc.to_df(statements[-1])   # Liefert einen DataFrame oder None (für 0 Ergebnisse)
        except Exception as e:
            return str(e)
        # Besteht aus ursprünglichem SQL-String und DataFrame 
        return KineticaSqlResponse(sql=text, dataframe=df)
    
    def parse_result(
        self, result: List[Generation], *, partial: bool = False
    ) -> KineticaSqlResponse:
        return self.parse(result[0].text)

    @property
    def _type(self) -> str:
        return "kinetica_sql_output_parser"