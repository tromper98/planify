from sqlalchemy.orm import registry

from src.common.framework.schema.schema import metadata

mapper_registry = registry(metadata=metadata)
Base = mapper_registry.generate_base()