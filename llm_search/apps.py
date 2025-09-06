import sys
import logging as log
from django.apps import AppConfig

logger = log.getLogger(__name__)


class LlmSearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "llm_search"

    def ready(self):
        # Avoid running during management commands where DB or app isn't fully ready
        skip_cmds = {"makemigrations", "migrate", "collectstatic", "shell", "test"}
        if any(c in sys.argv for c in skip_cmds):
            return

        try:
            from .vector_store import sync_articles

            logger.info("Starting LanceDB sync on app ready...")
            sync_articles()
        except Exception as e:
            # Do not block app startup if indexing fails; just log the error
            logger.exception("LanceDB sync failed: %s", e)
