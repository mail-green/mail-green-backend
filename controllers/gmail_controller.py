from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from logger import get_logger
from embedding_service import EmbeddingService
from gmail_service import fetch_message, process_batch
from tasks import embed_and_store_batch
import asyncio
import aiohttp
import time

router = APIRouter(prefix="/gmail", tags=["gmail"])
logger = get_logger("gmail_controller")
embedding_service = EmbeddingService()

@router.get('/messages/{msg_id}')
async def get_gmail_message(msg_id: str, request: Request):
    try:
        token = request.session.get('token')
        if not token:
            raise HTTPException(status_code=401, detail="로그인 필요")
        async with aiohttp.ClientSession() as session:
            msg = await fetch_message(session, msg_id, token)
        if not msg:
            logger.warning(f"메시지 {msg_id}를 찾을 수 없습니다.")
            raise HTTPException(status_code=404, detail="메시지 없음")
        return msg
    except Exception as e:
        logger.error(f"Gmail 메시지 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="서버 오류")

@router.get('/messages')
async def get_gmail_messages(request: Request, max_results: int = 10):
    try:
        token = request.session.get('token')
        if not token:
            raise HTTPException(status_code=401, detail="로그인 필요")
        
        # Gmail API로 메시지 목록 조회
        url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults={max_results}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Authorization": f"Bearer {token['access_token']}"}) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail=await resp.text())
                data = await resp.json()
                messages = data.get('messages', [])
        
        # 각 메시지 상세 정보 조회 및 임베딩
        results = await process_batch(messages, token)
        if not results:
            return {"messages": [], "info": "처리된 메시지 없음"}
            
        # 임베딩 및 저장
        embeddings = []
        for result in results:
            start_time = time.time()
            embedding = embedding_service.model.encode([result['clean']])[0]
            elapsed = time.time() - start_time
            embeddings.append({
                **result,
                "embedding": embedding.tolist()
            })
            logger.info(f"메시지 임베딩 완료 - 제목: {result['subject']} | 소요: {elapsed:.3f}초")
            
        # Chroma DB에 저장
        if embeddings:
            embedding_service.collection.add(
                ids=[e['id'] for e in embeddings],
                embeddings=[e['embedding'] for e in embeddings],
                metadatas=[{
                    "subject": e['subject'],
                    "from": e['from'],
                    "date": e['date']
                } for e in embeddings],
                documents=[e['clean'] for e in embeddings]
            )
            logger.info(f"총 {len(embeddings)}건의 메시지 임베딩 저장 완료")
            
        return {"messages": embeddings, "info": "임베딩 및 저장 완료"}
    except Exception as e:
        logger.error(f"Gmail 메시지 처리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/messages/all')
async def get_all_gmail_messages(request: Request):
    try:
        token = request.session.get('token')
        if not token:
            raise HTTPException(status_code=401, detail="로그인 필요")
            
        all_messages = []
        page_token = None
        
        while True:
            url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=500'
            if page_token:
                url += f'&pageToken={page_token}'
                
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"Authorization": f"Bearer {token['access_token']}"}) as resp:
                    if resp.status != 200:
                        raise HTTPException(status_code=resp.status, detail=await resp.text())
                    data = await resp.json()
                    
            messages = data.get('messages', [])
            all_messages.extend(messages)
            page_token = data.get('nextPageToken')
            logger.info(f"현재까지 {len(all_messages)}개 메일 ID 수집")
            
            if not page_token:
                break
        
        # 배치 처리를 위해 메시지 분할
        batch_size = 1000
        batches = [all_messages[i:i+batch_size] for i in range(0, len(all_messages), batch_size)]
        
        # Celery 태스크로 각 배치 처리
        for batch in batches:
            embed_and_store_batch.delay(batch, token)
            
        return {
            "message_count": len(all_messages),
            "info": f"{len(batches)}개 배치로 큐에 등록됨"
        }
    except Exception as e:
        logger.error(f"전체 Gmail 메시지 처리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/search')
async def search_gmail(query: str, n_results: int = 2):
    try:
        result = embedding_service.search(query, n_results)
        results = []
        for doc, meta, score in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
            results.append({
                "subject": meta["subject"],
                "similarity": 1 - score,
                "document": doc
            })
        return {"results": results}
    except Exception as e:
        logger.error(f"Gmail 검색 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 