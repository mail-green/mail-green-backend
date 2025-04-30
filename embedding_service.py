from sentence_transformers import SentenceTransformer
import chromadb
import os

def categorize_email(subject, body):
    text = (subject + " " + body).lower()
    if any(kw in text for kw in ["광고", "admob", "google ads", "크레딧", "할인", "쿠폰", "이벤트", "무료"]):
        return "promotion"
    elif any(kw in text for kw in ["스팸", "junk", "unsubscribe", "차단", "구독취소"]):
        return "spam"
    elif any(kw in text for kw in ["설문", "피드백", "만족도", "설문조사"]):
        return "survey"
    elif any(kw in text for kw in ["기능 업데이트", "신규 기능", "변경 사항", "약관 변경", "공지사항"]):
        return "notification"
    else:
        return "general"

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer("jhgan/ko-sbert-sts")

        def encode(self, texts, batch_size: int = 32):
            """
            Args:
                texts (List[str]): sentences to embed
                batch_size (int): encode batch size
            Returns:
                np.ndarray: normalized embedding vectors
            """
            return self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True
            )
        self.encode = encode.__get__(self)
        
        # ChromaDB 설정
        db_path = "./storage/chroma"
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=chromadb.Settings(
                allow_reset=True,
                is_persistent=True
            )
        )
        self.collection = self.client.get_or_create_collection("emails")

    def embed_and_store(self, emails):
        texts = [e["clean_text"] for e in emails]
        embeddings = self.encode(texts)
        self.collection.add(
            ids=[e["id"] for e in emails],
            embeddings=embeddings.tolist(),
            metadatas=[{
                "meta": {
                    "subject": e["subject"],
                    "from": e["from"],
                    "date": e["date"],
                    "category": categorize_email(e["subject"], e["clean_text"])
                }
            } for e in emails],
            documents=texts
        )

    def search(self, query, n_results=2):
        query_vec = self.encode([query])[0]
        result = self.collection.query(query_embeddings=[query_vec.tolist()], n_results=n_results)
        return result