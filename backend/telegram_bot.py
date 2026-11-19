"""
telegram_bot.py

Легковесный клиент и обработчик Telegram Bot API на базе httpx.
Обеспечивает:
- Отправку приветственных сообщений с кнопкой WebAppInfo(url=f"{PUBLIC_URL}/tma").
- Поддержку deep linking: /start pai_week_09 -> авто-переход в TMA на нужный курс и тему.
- Обработку webhook-запросов (POST /api/v1/tma/webhook).
- Безопасную работу в Offline / Dev режиме без реальных сетевых ошибок.
"""

import logging
from typing import Dict, Any, Optional
import httpx

from backend.config import settings

logger = logging.getLogger("themis.telegram_bot")


class TelegramBotService:
    """
    Легковесный асинхронный сервис взаимодействия с Telegram Bot API.
    """
    def __init__(
        self,
        bot_token: Optional[str] = None,
        public_url: Optional[str] = None,
        bot_username: Optional[str] = None
    ):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.public_url = (public_url or settings.PUBLIC_URL).rstrip("/")
        self.bot_username = bot_username or settings.TELEGRAM_BOT_USERNAME

    @property
    def is_dev_mode(self) -> bool:
        return self.bot_token in ("", "dev", "test")

    def build_tma_url(self, start_param: Optional[str] = None) -> str:
        """Формирует URL перехода в Telegram Mini App с параметрами темы."""
        base_url = f"{self.public_url}/tma"
        if start_param:
            # Преобразуем алиасы deep linking (pai_week_09 -> week_09_deep_learning)
            topic_param = start_param
            if "week_09" in start_param:
                topic_param = "week_09_deep_learning"
            return f"{base_url}?topic={topic_param}&start_param={start_param}"
        return base_url

    def build_inline_keyboard(self, start_param: Optional[str] = None) -> Dict[str, Any]:
        """Создает инлайн-клавиатуру Telegram с кнопкой запуска Web App."""
        tma_url = self.build_tma_url(start_param)
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "🚀 Открыть Themis Mini App",
                        "web_app": {"url": tma_url}
                    }
                ],
                [
                    {
                        "text": "🛡 О принципах UDL и защите балла",
                        "callback_data": "info_udl"
                    }
                ]
            ]
        }

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        """
        Отправка сообщения пользователю через Telegram Bot API.
        В DEV-режиме не производит сетевых вызовов, гарантируя надежность тестов.
        """
        if self.is_dev_mode:
            logger.info(f"[DEV BOT] Отправка сообщения в chat_id={chat_id}: {text[:60]}...")
            return {
                "ok": True,
                "result": {
                    "message_id": 99999,
                    "chat": {"id": chat_id, "type": "private"},
                    "text": text,
                }
            }

        api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(api_url, json=payload)
                data = resp.json()
                if not data.get("ok"):
                    logger.warning(f"Telegram Bot API error: {data}")
                return data
        except Exception as e:
            logger.error(f"Failed to send telegram message to {chat_id}: {e}")
            return {"ok": False, "error": str(e)}

    async def handle_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Главный диспетчер входящих обновлений webhook от Telegram Bot API.
        Поддерживает команды /start [payload], /help и inline callback.
        """
        # 1. Обработка текстовых сообщений
        message = update.get("message")
        if message:
            chat = message.get("chat", {})
            chat_id = chat.get("id")
            text = (message.get("text") or "").strip()
            user = message.get("from", {})
            user_name = user.get("first_name", "Студент")

            if not chat_id:
                return {"ok": True, "action": "ignored_no_chat_id"}

            # Команда /start с deep linking
            if text.startswith("/start"):
                parts = text.split(maxsplit=1)
                start_param = parts[1].strip() if len(parts) > 1 else None

                welcome_text = (
                    f"🎓 <b>Здравствуйте, {user_name}!</b>\n\n"
                    f"Добро пожаловать в <b>Themis Project</b> — сократический тьютор «Цифрового пандуса» "
                    f"для раскрытия вашего истинного понимания дисциплин.\n\n"
                    f"🛡 <b>Ваши гарантии психологической безопасности (UDL):</b>\n"
                    f"• <b>Zero Downward Penalty:</b> Очная оценка преподавателя зафиксирована и не может быть снижена ни при каких ответах.\n"
                    f"• <b>3 коротких шага:</b> Спокойный диалог с ИИ по ключевым понятиям лекции без спешки и стресса.\n"
                    f"• <b>Полная добровольность:</b> Возможность выйти в любой момент без сохранения сессии.\n\n"
                    f"Нажмите кнопку ниже, чтобы начать сократическую рефлексию:"
                )

                keyboard = self.build_inline_keyboard(start_param)
                await self.send_message(chat_id, welcome_text, reply_markup=keyboard)
                return {
                    "ok": True,
                    "action": "start_handled",
                    "chat_id": chat_id,
                    "start_param": start_param
                }

            # Команда /help
            elif text.startswith("/help"):
                help_text = (
                    f"ℹ️ <b>Справка Themis Project</b>\n\n"
                    f"Система позволяет доказать глубину знаний через сократическую рефлексию.\n\n"
                    f"• <b>Как это работает:</b> Тьютор задает 3 проблемных вопроса по теме недели.\n"
                    f"• <b>Ректификация:</b> Если понимание выше очной оценки, разница подлежит подтверждению преподавателем.\n"
                    f"• <b>Для старта:</b> Нажмите /start и откройте Mini App."
                )
                keyboard = self.build_inline_keyboard()
                await self.send_message(chat_id, help_text, reply_markup=keyboard)
                return {"ok": True, "action": "help_handled", "chat_id": chat_id}

            # Неизвестный текст — напоминаем о кнопке запуска
            else:
                reminder_text = (
                    f"Для запуска сократического диалога откройте Mini App по кнопке ниже:"
                )
                keyboard = self.build_inline_keyboard()
                await self.send_message(chat_id, reminder_text, reply_markup=keyboard)
                return {"ok": True, "action": "fallback_handled", "chat_id": chat_id}

        # 2. Обработка callback_query
        callback_query = update.get("callback_query")
        if callback_query:
            cq_id = callback_query.get("id")
            cb_data = callback_query.get("data")
            from_chat = callback_query.get("message", {}).get("chat", {})
            chat_id = from_chat.get("id")

            if cb_data == "info_udl" and chat_id:
                info_text = (
                    f"🛡 <b>Инварианты психометрической безопасности:</b>\n\n"
                    f"1. <b>Zero Downward Penalty:</b> Δ⁺ = max(0, S_depth - G_prof). "
                    f"Никаких отрицательных корректировок очной оценки!\n"
                    f"2. <b>Human-in-the-Loop:</b> Финальное аудиторское решение всегда принимает преподаватель.\n"
                    f"3. <b>Анти-зубрежка:</b> Оцениваются не заученные формулы, а системные связи понятий (SOLO Taxonomy)."
                )
                await self.send_message(chat_id, info_text, reply_markup=self.build_inline_keyboard())
                return {"ok": True, "action": "callback_handled", "callback_id": cq_id}

        return {"ok": True, "action": "unhandled_update_type"}


telegram_bot = TelegramBotService()
