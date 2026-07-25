# HelpeRP_Client/build_db.py
import json
import os
import re

def digitize_code_text(input_txt_path, output_json_path, code_name):
    """
    Автоматически оцифровывает массив сырого текста кодекса в структурированную базу данных.
    Ищет в тексте маркеры 'Статья X.' и разбивает их на поля.
    """
    if not os.path.exists(input_txt_path):
        # Создаем пустой демо-шаблон, если пользователь еще не закинул полный текст
        with open(input_txt_path, "w", encoding="utf-8") as f:
            f.write("Статья 105. Убийство\n1. Умышленное причинение смерти другому человеку - наказывается...\n\n")
            f.write("Статья 228. Незаконный оборот\n1. Приобретение, хранение без цели сбыта - наказывается...\n")
        print(f"[Парсер] Создан пустой шаблон {input_txt_path}. Наполните его сырым текстом из Консультант+!")

    with open(input_txt_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Регулярное выражение для поиска статей формата "Статья 105. Название"
    articles_found = re.split(r'(?=Статья\s+\d+(?:\.\d+)?\.)', raw_text)
    
    database = []
    
    for block in articles_found:
        block = block.strip()
        if not block:
            continue
            
        lines = block.split("\n")
        header = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        
        # Вытаскиваем номер статьи
        match_num = re.search(r'Статья\s+(\d+(?:\.\d+)?)', header)
        if match_num:
            art_num = match_num.group(1)
            # Извлекаем чистое название статьи
            title = header.replace(f"Статья {art_num}.", "").strip()
            
            # Определяем, является ли статья частой для RP-процессов
            frequent_articles = ["105", "111", "158", "161", "162", "213", "228", "228.1", "285", "317", "19.3", "20.1"]
            is_freq = art_num in frequent_articles
            
            database.append({
                "article": art_num,
                "title": f"Статья {art_num}. {title}",
                "code": code_name,
                "description": body,
                "is_frequent": is_freq,
                "keywords": [art_num, title.lower()]
            })

    # Сохраняем оцифрованный кодекс в нашу системную папочку data
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Оцифровано элементов: {len(database)} и сохранено в {output_json_path}")

if __name__ == "__main__":
    # Демонстрация сборки полной базы законодательства
    digitize_code_text("raw_uk_rf.txt", "data/legislation_rf.json", "УК РФ")
