import aiohttp
from email_utils import clean_text
import asyncio

async def fetch_message(session, msg_id, token):
    url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}'
    headers = {"Authorization": f"Bearer {token['access_token']}"}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            headers = data.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
            snippet = data.get('snippet', '')
            return {
                'id': msg_id,
                'subject': subject,
                'from': from_email,
                'date': date,
                'clean': clean_text(subject + " " + snippet)
            }
        else:
            return None

async def process_batch(batch, token):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_message(session, message['id'], token) for message in batch if isinstance(message, dict) and 'id' in message]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None] 