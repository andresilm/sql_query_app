import abc

class IQuerySqlTranslationModel(abc.ABC):
    @abc.abstractmethod
    def question_to_sql(question: str, schema: str) -> str:
        """
        Translates a natural language question into an SQL query based on the provided schema.

        Args:
            question (str): The natural language question to be translated.
            schema (str): The database schema to be used for generating the SQL query.

        Returns:
            str: The translated SQL query.
        """
        pass

