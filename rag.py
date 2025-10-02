import json
import uuid
from typing import List, Dict, Any, Iterable, Tuple
import re, pathlib
import orjson
from slugify import slugify
from pinecone import Pinecone
import tiktoken

# ------------------------------ Config ------------------------------
PINECONE_KEY = 'pcsk_E4cUN_2MHd1oUx2Bvz7yTh1WiMnteu4Z8Mj2i3hraZ4yTKpuFv3fuikisrwXtX9sVaf1U'
PINECONE_HOST = "https://developer-quickstart-py-02jjq2u.svc.aped-4627-b74a.pinecone.io"

pc = Pinecone(api_key=PINECONE_KEY)
index = pc.Index("developer-quickstart-py")

SECTION_FIELDS = [
    ("Level", ["basicDetails.level.label"]),
    ("Category", ["basicDetails.schemeSubCategory", "basicDetails.schemeCategory"]),
    ("Target Beneficiaries", ["basicDetails.targetBeneficiaries"]),
    ("DBT Scheme", ["basicDetails.dbtScheme"]),
    ("Implementing Agency", ["basicDetails.implementingAgency"]),
    ("Tags", ["basicDetails.tags"]),
    ("Open Date", ["basicDetails.schemeOpenDate"]),
    ("Close Date", ["basicDetails.schemeCloseDate"]),
    ("Brief Description", ["schemeContent.briefDescription"]),
    ("Detailed Description", ["schemeContent.detailedDescription_md"]),
    ("Eligibility", ["eligibilityCriteria.eligibilityDescription_md"]),
    ("Official Links", ["schemeContent.references"]),
]

# ------------------------------ Utils ------------------------------

def read_any_json(path: str) -> List[Dict[str, Any]]:
    """Read JSON or JSONL file"""
    raw = pathlib.Path(path).read_bytes()
    try:
        data = orjson.loads(raw)
        if isinstance(data, list): return data
        if isinstance(data, dict): return [data]
    except Exception:
        items = [orjson.loads(ln) for ln in raw.splitlines() if ln.strip()]
        return items
    return []

def stringify(v: Any) -> str:
    """Convert values to string safely"""
    if v is None:
        return ""
    if isinstance(v, (str, int, float, bool)):
        return str(v)
    if isinstance(v, dict) and "label" in v:
        return str(v["label"])
    if isinstance(v, dict) and "value" in v:
        return str(v["value"])
    try:
        return orjson.dumps(v).decode("utf-8")
    except Exception:
        return str(v)

def collect_flat_texts(flat: dict, prefix: str, numbered: bool = False) -> str:
    """Collect flattened values by prefix and join them as bullets/numbered list."""
    texts = []
    for k, v in flat.items():
        if isinstance(k, str) and k.startswith(prefix) and k.endswith(".text"):
            s = stringify(v).strip()
            if s:
                texts.append(s)

    if not texts:
        return ""

    if numbered:
        return "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    return "\n".join(f"- {t}" for t in texts)

def flatten(obj: Any, parent_key: str = "", sep=".") -> Dict[str, Any]:
    """Flatten nested dicts/lists"""
    items = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items.extend(flatten(v, new_key, sep=sep).items())
    elif isinstance(obj, list):
        if all(isinstance(x, dict) for x in obj):
            for i, v in enumerate(obj):
                items.extend(flatten(v, f"{parent_key}[{i}]", sep=sep).items())
        else:
            items.append((parent_key, ", ".join([stringify(x) for x in obj])))
    else:
        items.append((parent_key, obj))
    return dict(items)

def pick_first(flat: Dict[str, Any], keys: List[str]) -> str:
    """Return first available non-empty value"""
    for k in keys:
        if k in flat and stringify(flat[k]).strip():
            return stringify(flat[k]).strip()
    return ""

# ------------------------------ RAG Builder ------------------------------

def make_rag_text(flat: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Make RAG-friendly Markdown text and metadata"""
    title = pick_first(flat, ["basicDetails.schemeName", "schemeShortTitle", "title"])
    ministry = pick_first(flat, ["basicDetails.nodalMinistryName.label"])
    dept = pick_first(flat, ["basicDetails.nodalDepartmentName.label"])

    lines = []
    if title:
        lines.append(f"# {title}")
    header_bits = [x for x in [ministry, dept] if x]
    if header_bits:
        lines.append(f"_{' • '.join(header_bits)}_")
    lines.append("")

    # generic sections
    for section, keys in SECTION_FIELDS:
        val = pick_first(flat, keys)
        if val:
            lines.append(f"## {section}\n{val}")

    # benefits
    b_type = pick_first(flat, ["schemeContent.benefitTypes.label"])
    b_list = collect_flat_texts(flat, "schemeContent.benefits[")
    if b_type or b_list:
        parts = []
        if b_type:
            parts.append(b_type)
        if b_list:
            parts.append(b_list)
        lines.append("## Benefits\n" + "\n\n".join(parts))

    # application process
    app_steps = collect_flat_texts(flat, "applicationProcess[0].process[", numbered=True)
    app_url = pick_first(flat, ["applicationProcess[0].url", "applicationProcess.url"])
    if app_steps or app_url:
        body = []
        if app_steps:
            body.append(app_steps)
        if app_url:
            body.append(app_url)
        lines.append("## Application Process\n" + "\n\n".join(body))

    # documents
    docs_text = collect_flat_texts(flat, "application.documents[")
    if not docs_text:
        docs_text = collect_flat_texts(flat, "applicationProcess[0].documents[")
    if not docs_text:
        docs_text = collect_flat_texts(flat, "schemeContent.documentsRequired[")
    if docs_text:
        lines.append("## Documents Required\n" + docs_text)

    metadata = {
        "title": title or "",
        "ministry": ministry or "",
        "department": dept or "",
    }
    text = "\n\n".join(lines).strip()
    return text, metadata

def chunk_text(text: str, max_tokens=512, overlap_tokens=40) -> List[str]:
    """Split text into overlapping chunks"""
    sentences = re.split(r'(?<=[\.!?])\s+', text.strip())
    chunks, cur, cur_tok = [], [], 0
    for sent in sentences:
        t = count_tokens(sent)
        if cur_tok + t > max_tokens and cur:
            chunks.append(" ".join(cur).strip())
            # add overlap
            if overlap_tokens > 0 and chunks[-1]:
                tail = chunks[-1].split()
                keep = max(1, len(tail) - overlap_tokens//2)
                cur = [" ".join(tail[keep:])]
                cur_tok = count_tokens(cur[0])
            else:
                cur, cur_tok = [], 0
        cur.append(sent)
        cur_tok += t
    if cur:
        chunks.append(" ".join(cur).strip())
    return [c for c in chunks if c]

def count_tokens(s: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(s))

def build_docs_from_file(in_path: str) -> List[Dict[str, Any]]:
    """Build RAG docs from input file"""
    records = read_any_json(in_path)
    docs = []
    for rec in records:
        flat = flatten(rec)
        text, meta = make_rag_text(flat)
        base_id = slugify("-".join([meta.get("title",""), meta.get("ministry",""), meta.get("department","")])[:80]) or str(uuid.uuid4())
        chunks = chunk_text(text, max_tokens=512, overlap_tokens=40)
        for idx, ch in enumerate(chunks):
            docs.append({
                "id": f"{base_id}--{idx:04d}",
                "text": ch,
                "metadata": meta | {"chunk_index": idx, "source_id": base_id}
            })
    return docs

def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]):
    with open(path, "wb") as f:
        for row in rows:
            f.write(orjson.dumps(row))
            f.write(b"\n")

def export_jsonl(docs: List[Dict[str, Any]], out_path: str = "rag.jsonl"):
    """Export docs to JSONL"""
    write_jsonl(out_path, docs)
    print(f"Wrote {len(docs)} chunks to {out_path}")

# ------------------------------ Pinecone Upsert ------------------------------

def clean_chunk_text(raw_text: str) -> str:
    """Clean raw chunk text by removing HTML tags like <br>."""
    if not raw_text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", raw_text, flags=re.IGNORECASE)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()

def upsert_to_pinecone(batch_size: int = 96):
    """Upsert records to Pinecone with managed embeddings (batched)"""
    records = []
    with open("rag.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            clean_text = clean_chunk_text(rec["text"])
            record = {
                "_id": rec["id"],
                "chunk_text": clean_text,
                **rec.get("metadata", {})
            }
            records.append(record)

    print(f"Loaded {len(records)} records from rag.jsonl")

    # Batch upload to avoid Pinecone 96 limit
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        index.upsert_records(
            namespace="schemes-v1",
            records=batch
        )
        print(f"✅ Upserted batch {i//batch_size + 1} with {len(batch)} records")

    print("🎉 All records upserted successfully.")

# ------------------------------ Main ------------------------------

if __name__ == "__main__":
    docs = build_docs_from_file("schemeData.json")
    export_jsonl(docs, "rag.jsonl")
    upsert_to_pinecone()
