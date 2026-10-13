import structlog

logger = structlog.get_logger("embedding")


def log_embedding_configuration(settings) -> None:
    """State which embedding provider is active, never the credentials."""
    logger.info(
        "embedding_configuration",
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_dimension=settings.embedding_dimension,
    )
