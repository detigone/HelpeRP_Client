# HelpeRP_Client/core/online_search.py
import urllib.request
import urllib.parse
import re
import json

def search_law_online(query: str, faction_context: str = "Законодательство РФ") -> str:
    """
    Выполняет быстрый поиск по открытым базам данных законов или памяток в интернете.
    Возвращает текст найденной статьи или регламента.
    """
    # Добавляем контекст для поискового робота, чтобы он искал именно законы или RP-форумы
    full_query = f"{faction_context} {query}"
    
    # Кодируем запрос для безопасной передачи в URL
    encoded_query = urllib.parse.quote(full_query)
    
    # Используем бесплатное API для быстрого поиска текстовых выдержек
    url = f"https://duckduckgo.com{encoded_query}"
    
    try:
        # Маскируемся под обычный браузер, чтобы сайты не блокировали запросы программы
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=4) as response:
            html = response.read().decode('utf-8')
            
        # Вытаскиваем текстовые сниппеты (краткое содержание) с сайтов результатов
        # Нам нужны блоки с описанием страниц
        snippets = re.findall(r'<a class="result__snippet".*?>(.*?)</a>', html, re.DOTALL)
        
        if not snippets:
            return ""
            
        # Очищаем найденный текст от HTML-тегов
        clean_results = []
        for snip in snippets[:3]: # Берем топ-3 самых точных ответа из интернета
            text = re.sub(r'<[^>]+>', '', snip) # Удаляем теги
            text = text.replace('&quot;', '"').replace('&amp;', '&').strip()
            clean_results.append(text)
            
        return "\n\n--- Найдено в сети ---\n" + "\n... ".join(clean_results)
        
    except Exception as e:
        print(f"[Online Search] Ошибка веб-поиска: {e}")
        return ""
