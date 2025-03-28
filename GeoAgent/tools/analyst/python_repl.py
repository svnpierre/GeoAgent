# Anpassungen von https://python.langchain.com/api_reference/_modules/langchain_experimental/utilities/python.html#PythonREPL
# Ermöglicht die Ausführung eines Python-Skripts. Wird mit python_repl.run("code") gestartet und liefert immer ein Dict mit den Schlüsseln code, error, result als String "{"result":str, code:"str", "error":str}" zurück. . 

import functools
import logging
import multiprocessing
import re
import sys
from io import StringIO
from typing import Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

@functools.lru_cache(maxsize=None)
def warn_once() -> None:
    """Warn once about the dangers of PythonREPL."""
    logger.warning("Python REPL can execute arbitrary code. Use with caution.")

class PythonREPL(BaseModel):
    """Simulates a standalone Python REPL."""

    globals: Optional[Dict] = Field(default_factory=dict, alias="_globals")
    locals: Optional[Dict] = Field(default_factory=dict, alias="_locals")

    @staticmethod
    def sanitize_input(query: str) -> str:
        """Sanitize input to the python REPL.

        Remove whitespace, backtick & python
        (if llm mistakes python console as terminal)

        Args:
            query: The query to sanitize

        Returns:
            str: The sanitized query
        """
        query = re.sub(r"^(\s|`)*(?i:python)?\s*", "", query)
        query = re.sub(r"(\s|`)*$", "", query)
        return query

    @classmethod
    def worker(
        cls,
        command: str,
        globals: Optional[Dict],
        locals: Optional[Dict],
        queue: multiprocessing.Queue,
    ) -> None:
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        result = {"result": None, "code": command, "error": None}
        try:
            cleaned_command = cls.sanitize_input(command)
            exec(cleaned_command, globals, locals)
            result["result"] = mystdout.getvalue()
        except Exception as e: 
            result["error"] = repr(e)
        finally:
            sys.stdout = old_stdout
            queue.put(str(result)) # dict als string ausgeben z.B. '{\'result\': None, \'code\': \'print(zahl1+c)\', \'error\': \'TypeError("unsupported operand type(s) for +: \\\'int\\\' and \\\'str\\\'")\'}'

    def run(self, command: str, timeout: Optional[int] = None) -> str:
        """Run command with own globals/locals and returns anything printed.
        Timeout after the specified number of seconds."""

        # Warn against dangers of PythonREPL
        warn_once()

        queue: multiprocessing.Queue = multiprocessing.Queue()

        # Only use multiprocessing if we are enforcing a timeout
        if timeout is not None:
            # create a Process
            p = multiprocessing.Process(
                target=self.worker, args=(command, self.globals, self.locals, queue)
            )

            # start it
            p.start()

            # wait for the process to finish or kill it after timeout seconds
            p.join(timeout)

            if p.is_alive():
                p.terminate()
                return "Execution timed out"
        else:
            self.worker(command, self.globals, self.locals, queue)
        # get the result from the worker function
        return queue.get()

