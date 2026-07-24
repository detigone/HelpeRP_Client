# HelpeRP_Client/core/ai_client.py
import openai
from core.config import app_config

class AIClient:
    def __init__(self):
        self.client = None
        self.update_client()

    def update_client(self):
        """Обновляет настройки подключения, если пользователь изменил ключ или сервер в конфиге"""
        api_key = app_config.get("api_key")
        base_url = app_config.get("base_url")
        
        # Инициализируем стандартный клиент OpenAI, который поддерживает большинство провайдеров
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def generate_rp_commands(self, user_situation: str) -> list:
        """
        Отправляет ситуацию в ИИ и возвращает готовый список строк для отправки в чат.
        Автоматически учитывает текущую фракцию и характер персонажа из настроек.
        """
        faction = app_config.get("current_faction", "МВД")
        char_data = app_config.get("character", {})
        model = app_config.get("model", "gpt-4o-mini")
        
        # Формируем жесткие правила для ИИ, чтобы он выдавал только команды для игры
        system_prompt = (
            f"Ты — ИИ-модуль генерации отыгровок для RolePlay серверов (GTA 5 RP, SAMP, CRMP).\n"
            f"Действуй от лица персонажа фракции: {faction}.\n"
            f"Данные персонажа: Имя {char_data.get('name')}, Звание/Роль: {char_data.get('rank')}, Значок/Жетон: {char_data.get('badge')}.\n"
            f"Характер и особенности речи: {char_data.get('personality')}.\n\n"
            f"КРИТИЧЕСКИЕ ПРАВИЛА:\n"
            f"1. Выдавай ТОЛЬКО строки команд для игрового чата (/me, /do, /try, /todo) или реплики персонажа.\n"
            f"2. Каждая команда или реплика должна быть на НОВОЙ строке.\n"
            f"3. Не пиши никаких приветствий, пояснений, списков, кавычек или лишних символов Markdown. Только чистые строки чата.\n"
            f"4. Команда /me пишется с маленькой буквы. Действия должны соответствовать характеру."
        )

        try:
            # Если настройки изменились на лету, обновляем клиент перед запросом
            self.update_client()
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Сгенерируй отыгровку для ситуации: {user_situation}"}
                ],
                temperature=0.6 # Небольшая температура, чтобы отыгровки были адекватными и строгими
            )
            
            # Получаем текст, чистим от лишних пробелов и разбиваем по строкам
            raw_text = response.choices.message.content.strip()
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
            return lines
            
        except Exception as e:
            print(f"[HelpeRP AI] Ошибка генерации: {e}")
            return [f"/do Произошел технический сбой ИИ-модуля (Ошибка: {str(e)[:30]})."]

# Создаем глобальный объект ИИ-клиента
rp_ai = AIClient()
