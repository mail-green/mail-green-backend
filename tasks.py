from celery import Celery
from embedding_service import EmbeddingService
from gmail_service import process_batch
from logger import get_logger
from config import Config as AppConfig
import asyncio

celery_app = Celery(
    "tasks",
    broker=AppConfig.REDIS_URL,
    backend=AppConfig.REDIS_URL
)

embedding_service = EmbeddingService()
logger = get_logger("tasks")

@celery_app.task
def embed_and_store_batch(batch, token):
    import time
    if not batch:
        logger.warning("빈 배치가 전달되었습니다.")
        return
    if not token or 'access_token' not in token:
        logger.warning("유효하지 않은 토큰이 전달되었습니다.")
        return
    try:
        results = asyncio.run(process_batch(batch, token))
        if not results:
            logger.warning("처리된 메시지가 없습니다.")
            return
        start_time = time.time()
        msg_ids = [r['id'] for r in results]
        cleans = [r['clean'] for r in results]
        metas = [{"subject": r['subject'], "from": r['from'], "date": r['date']} for r in results]
        logger.info(f"임베딩 시작: {len(cleans)}개 텍스트")
        embeddings = embedding_service.encode(cleans)
        logger.info(f"임베딩 완료: {len(embeddings)}개 벡터")
        embedding_service.collection.add(
            ids=msg_ids,
            embeddings=[vec.tolist() for vec in embeddings],
            metadatas=metas,
            documents=cleans,
        )
        elapsed = time.time() - start_time
        logger.info(f"batch {len(results)}건 저장 완료 | 소요: {elapsed:.3f}초")
    except Exception as e:
        logger.error(f"배치 처리 중 오류 발생: {e}", exc_info=True)