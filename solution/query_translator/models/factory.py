from .sqlcoder2_wrapper import SqlCoder2Wrapper
from .t5_small_sql_wrapper import T5SmallSqlWrapper
import logging
from ..models.query_translation_model import IQuerySqlTranslationModel

logger = logging.getLogger(__name__)


def get_translation_model(is_cuda_available: bool) -> IQuerySqlTranslationModel:
    if is_cuda_available:
        logger.info('Will load LLM model %s', "defog/sqlcoder-7b-2")
        model = SqlCoder2Wrapper()
    else:
        logger.info('Will load LLM model %s', "cssupport/t5-small-awesome-text-to-sql")
        model = T5SmallSqlWrapper()

    return model
