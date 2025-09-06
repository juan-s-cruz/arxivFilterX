"""Vector store utilities for LanceDB-backed semantic search.

This module builds and maintains a local LanceDB table from the
`webFilter.Article` Django model and exposes a simple search interface.

It is designed to:
  * Create the LanceDB table on first run (under ``data/lancedb``).
  * Incrementally add vectors for any new Article rows on subsequent runs.
  * Provide a lightweight text search over vector similarity.

Embeddings are produced with a compact bi-encoder (MiniLM) using mean pooling
and L2 normalization, suitable for cosine-similarity search.
"""

import os
import logging as log
from typing import List, Dict, Any

import numpy as np
import torch
import lancedb

# from django.conf import settings
from transformers import AutoModel, AutoTokenizer


logging = log.getLogger(__name__)


# Lightweight sentence embedding using a HF bi-encoder model
_EMBED_MODEL_NAME = "llm_search/models/all-MiniLM-L6-v2"
_embedder_model = None
_embedder_tokenizer = None


def _get_embedder():
    """Return cached tokenizer and model for sentence embeddings.

    Loads the tokenizer and model on first call and reuses them afterwards.
    If CUDA is available, the model is moved to GPU and set to eval mode.

    Returns:
        Tuple[transformers.PreTrainedTokenizer, torch.nn.Module]:
        The tokenizer and the embedding model.
    """
    global _embedder_model, _embedder_tokenizer
    if _embedder_model is None or _embedder_tokenizer is None:
        _embedder_tokenizer = AutoTokenizer.from_pretrained(
            _EMBED_MODEL_NAME, repo_type="local"
        )
        _embedder_model = AutoModel.from_pretrained(_EMBED_MODEL_NAME)
        _embedder_model.eval()
        if torch.cuda.is_available():
            _embedder_model = _embedder_model.to("cuda")
            logging.info("Using CUDA for embedding model.")
        else:
            logging.info("CUDA not available; using CPU for embedding model.")
    return _embedder_tokenizer, _embedder_model


@torch.no_grad()
def _embed_texts(texts: List[str], batch_size: int = 64) -> np.ndarray:
    """Embed a list of texts into L2-normalized vectors.

    Uses mean pooling over token embeddings (masked by attention) and L2
    normalizes the result, which aligns with cosine-similarity search.

    Args:
        texts: Input strings to embed.
        batch_size: Number of texts processed per forward pass.

    Returns:
        np.ndarray: Array of shape (len(texts), D), where D is the hidden size
        of the transformer model (384 for MiniLM). Returns an empty array with
        shape (0, 384) when ``texts`` is empty.
    """
    tokenizer, model = _get_embedder()
    all_vecs: List[np.ndarray] = []
    device = next(model.parameters()).device

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(device)
        outputs = model(**encoded)
        token_embeddings = outputs.last_hidden_state  # (B, T, H)
        attention_mask = encoded.attention_mask  # (B, T)

        # Mean pooling with attention mask
        mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        summed = torch.sum(token_embeddings * mask, dim=1)
        counts = torch.clamp(mask.sum(dim=1), min=1e-9)
        embeddings = summed / counts

        # L2 normalize
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        all_vecs.append(embeddings.detach().cpu().numpy())

    return np.vstack(all_vecs) if all_vecs else np.zeros((0, 384), dtype=np.float32)


def _get_lancedb_path() -> str:
    """Return the on-disk LanceDB directory and ensure it exists.

    Returns:
        str: Absolute path to the LanceDB directory under
        ``data/lancedb``.
    """
    # base = settings.BASE_DIR
    db_dir = os.path.join("data", "lancedb")
    os.makedirs(db_dir, exist_ok=True)
    return db_dir


def _ensure_lancedb():
    """Connect to the LanceDB database stored under ``data/lancedb``.

    Returns:
        lancedb.db.LanceDBConnection: An active LanceDB connection.
    """
    path = _get_lancedb_path()
    return lancedb.connect(path)


def _fetch_articles() -> List[Dict[str, Any]]:
    """Fetch articles from the ORM as plain dicts.

    Concatenates title and abstract into a single ``text`` field for embedding
    while keeping other relevant metadata for filtering and display.

    Returns:
        List[Dict[str, Any]]: Records with keys
        ``id, text, title, authors, pub_date, url, rank``.
    """
    # Import locally to avoid import-time coupling
    from webFilter.models import Article

    # Selecting only needed fields keeps memory smaller
    qs = Article.objects.all().values(
        "id", "title_text", "abstract", "authors", "pub_date", "real_url", "rank"
    )
    docs: List[Dict[str, Any]] = []
    for a in qs.iterator():
        # Concatenate title and abstract for embedding
        text = (
            f"{a['title_text']}\n\n{a['abstract']}"
            if a["abstract"]
            else a["title_text"]
        )
        docs.append(
            {
                "id": int(a["id"]),
                "text": text,
                "title": a["title_text"],
                "authors": a["authors"],
                "pub_date": str(a["pub_date"]),
                "url": a["real_url"],
                "rank": float(a["rank"]) if a["rank"] is not None else 0.0,
            }
        )
    return docs


def sync_articles(table_name: str = "articles") -> None:
    """Sync LanceDB with the latest rows in SQLite.

    Behavior:
        * First run: embed all articles and create the LanceDB table.
        * Subsequent runs: find missing IDs, embed and append only new rows.

    Args:
        table_name: Name of the LanceDB table to create or update.

    Limitations:
        This function does not update vectors for modified rows. If article
        content changes are expected, consider adding a last-modified timestamp
        or content hash and switching to an upsert strategy.
    """
    db = _ensure_lancedb()

    # Determine if table exists
    existing_tables = set(db.table_names())
    docs = _fetch_articles()
    if not docs:
        logging.info("LanceDB sync: no articles to index.")
        return

    if table_name not in existing_tables:
        # First-time creation: embed all and create table
        texts = [d["text"] for d in docs]
        vectors = _embed_texts(texts)
        for i, d in enumerate(docs):
            d["vector"] = vectors[i].astype(np.float32)

        tbl = db.create_table(table_name, data=docs, mode="overwrite")
        logging.info(
            "LanceDB sync: created table '%s' with %d articles.", table_name, len(docs)
        )
        return

    # Incremental: add missing ids
    tbl = db.open_table(table_name)
    try:
        ids_in_tbl = set(map(int, tbl.to_pandas().id.tolist()))
    except Exception:
        # Fallback if to_pandas limited; read all rows
        try:
            arrow_tbl = tbl.to_arrow()
            ids = arrow_tbl.to_pydict().get("id", [])
            ids_in_tbl = set(map(int, ids))
        except Exception:
            # Last resort: initialize empty set
            ids_in_tbl = set()

    missing: List[Dict[str, Any]] = [d for d in docs if d["id"] not in ids_in_tbl]

    if not missing:
        logging.info("LanceDB sync: table '%s' already up to date.", table_name)
        return

    texts = [d["text"] for d in missing]
    vectors = _embed_texts(texts)
    for i, d in enumerate(missing):
        d["vector"] = vectors[i].astype(np.float32)

    tbl.add(missing)
    logging.info(
        "LanceDB sync: added %d new articles to '%s' (now ~%d).",
        len(missing),
        table_name,
        len(ids_in_tbl) + len(missing),
    )


def search(
    query: str, k: int = 5, table_name: str = "articles"
) -> List[Dict[str, Any]]:
    """Run a semantic search against the LanceDB table.

    Args:
        query: Natural-language query to embed and search.
        k: Number of nearest neighbors to return.
        table_name: LanceDB table name.

    Returns:
        List[Dict[str, Any]]: Top-k records ordered by similarity (closest
        first), including metadata and distance fields.
    """
    db = _ensure_lancedb()
    tbl = db.open_table(table_name)
    q_vec = _embed_texts([query])[0]
    results = tbl.search(q_vec, ordering_field_name="pub_date").limit(k).to_list()
    return results
