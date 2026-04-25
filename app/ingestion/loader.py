import os
import logging
from app.models.schemas import Document

logger = logging.getLogger(__name__)


def load_documents(folder_path: str):
    documents = []

    if not os.path.isdir(folder_path):
        logger.warning("Input folder does not exist: %s", folder_path)
        return documents

    for i, file in enumerate(sorted(os.listdir(folder_path))):
        if file.endswith(".txt") or file.endswith(".md"):
            path = os.path.join(folder_path, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            documents.append(
                Document(
                    id=str(i),
                    type=None,
                    content=content,
                    source_file=file
                )
            )
            logger.debug("Loaded document: %s", file)

    return documents
