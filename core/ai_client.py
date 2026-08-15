# HelpeRP_Client/core/ai_client.py

import openai

from core.ai_providers import provider_label
from core.config import app_config, effective_api_key, normalize_base_url


class AIClientError(Exception):
    pass


class AIClient:
    def __init__(self):
        self.client = None
        self.update_client()

    def _resolve_api_key(self) -> str:
        """Единая точка получения эффективного API-ключа из конфига."""
        return effective_api_key(
            app_config.get("api_key", ""),
            app_config.get("base_url", ""),
            app_config.get("ai_provider", ""),
        )

    def update_client(self):
        api_key = self._resolve_api_key()
        base_url = normalize_base_url(app_config.get("base_url", ""))
        if not api_key:
            self.client = None
            return
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def _provider_name(self) -> str:
        pid = app_config.get("ai_provider", "")
        if pid:
            return provider_label(pid)
        return "API"

    def test_connection(self) -> tuple[bool, str]:
        """Проверка API. Возвращает (ok, message)."""
        if not self._resolve_api_key():
            return False, "Укажите API-ключ в настройках"
        try:
            self.update_client()
            model = app_config.get("model", "gpt-4o-mini")
            self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True, f"{self._provider_name()} · {model}"
        except Exception as e:
            return False, str(e)[:120]

    def generate_rp_commands(self, user_situation: str) -> list:
        if not self._resolve_api_key():
            raise AIClientError("API-ключ не настроен. Откройте Настройки → ИИ.")

        from core.characters import get_active_character

        faction = app_config.get("current_faction", "МВД")
        char_data = get_active_character()
        model = app_config.get("model", "gpt-4o-mini")

        system_prompt = (
            f"Ты — ИИ-модуль генерации отыгровок для RolePlay серверов (GTA 5 RP, SAMP, CRMP).\n"
            f"Действуй от лица персонажа фракции: {faction}.\n"
            f"Данные персонажа: Имя {char_data.get('name')}, Звание/Роль: {char_data.get('rank')}, "
            f"Значок/Жетон: {char_data.get('badge')}.\n"
            f"Характер и особенности речи: {char_data.get('personality')}.\n\n"
            f"КРИТИЧЕСКИЕ ПРАВИЛА:\n"
            f"1. Выдавай ТОЛЬКО строки команд для игрового чата (/me, /do, /try, /todo) или реплики персонажа.\n"
            f"2. Каждая команда или реплика должна быть на НОВОЙ строке.\n"
            f"3. Не пиши приветствий, пояснений, markdown. Только чистые строки чата.\n"
            f"4. Команда /me пишется с маленькой буквы."
        )

        self.update_client()
        if not self.client:
            raise AIClientError("Не удалось инициализировать AI-клиент")

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Сгенерируй отыгровку для ситуации: {user_situation}"},
            ],
            temperature=0.6,
        )

        raw_text = response.choices[0].message.content.strip()
        for ch in ("```", "**", "`"):
            raw_text = raw_text.replace(ch, "")
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        if not lines:
            raise AIClientError("ИИ вернул пустой ответ")
        return lines


rp_ai = AIClient()
