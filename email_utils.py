import re

def clean_text(text: str) -> str:
    text = re.sub(r'\S+@\S+', '', text)  # 이메일 제거
    text = re.sub(r'\d{2,4}-\d{3,4}-\d{4}', '', text)  # 전화번호 제거
    return text 