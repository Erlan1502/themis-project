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
import asyncio
from typing import Dict, Any, Optional, Callable
import httpx

from backend.config import settings
from backend.database import (
    get_telegram_binding_token,
    mark_binding_token_used,
    link_telegram_identity,
    get_student_identity,
)

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
        self._bot_token = bot_token
        self._public_url = public_url.rstrip("/") if public_url else None
        self._bot_username = bot_username
        self._binding_callback: Optional[Callable] = None
        self._is_polling: bool = False

    @property
    def bot_token(self) -> str:
        return self._bot_token or settings.TELEGRAM_BOT_TOKEN

    @bot_token.setter
    def bot_token(self, value: Optional[str]):
        self._bot_token = value

    @property
    def public_url(self) -> str:
        url = self._public_url or settings.PUBLIC_URL or "http://localhost:8000"
        return url.rstrip("/")

    @public_url.setter
    def public_url(self, value: Optional[str]):
        self._public_url = value.rstrip("/") if value else None

    @property
    def bot_username(self) -> str:
        return self._bot_username or settings.TELEGRAM_BOT_USERNAME

    @bot_username.setter
    def bot_username(self, value: Optional[str]):
        self._bot_username = value

    async def delete_webhook(self, drop_pending_updates: bool = False) -> Dict[str, Any]:
        """
        Удаление текущего вебхука Telegram Bot API перед запуском Long Polling.
        """
        if self.is_dev_mode:
            logger.info("[DEV BOT] deleteWebhook пропущен в DEV/Test режиме.")
            return {"ok": True, "result": True}

        api_url = f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(api_url, json={"drop_pending_updates": drop_pending_updates})
                data = resp.json()
                logger.info(f"Telegram deleteWebhook response: {data}")
                return data
        except Exception as e:
            logger.warning(f"Failed to delete Telegram webhook: {e}")
            return {"ok": False, "error": str(e)}

    async def start_polling(self, timeout: int = 10):
        """
        Запуск фонового цикла Long Polling (getUpdates).
        Гарантирует работу бота на локальном сервере (localhost) без публичного IP или туннеля.
        Снимает вебхук и непрерывно получает апдейты от Telegram серверов.
        """
        if self.is_dev_mode:
            logger.info("[DEV BOT] Long Polling пропущен (DEV/Test режим).")
            return

        logger.info(f"Запуск Telegram Bot Long Polling для @{self.bot_username}...")
        # Снимаем активный webhook, чтобы Telegram начал отдавать апдейты через getUpdates
        await self.delete_webhook(drop_pending_updates=False)

        self._is_polling = True
        offset = 0

        async with httpx.AsyncClient(timeout=float(timeout + 15)) as client:
            while self._is_polling:
                try:
                    url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
                    resp = await client.get(url, params={"offset": offset, "timeout": timeout})
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("ok"):
                            updates = data.get("result", [])
                            for update in updates:
                                uid = update.get("update_id")
                                if uid is not None:
                                    offset = max(offset, uid + 1)
                                try:
                                    await self.handle_update(update)
                                except Exception as handle_err:
                                    logger.error(f"Ошибка при обработке update {uid}: {handle_err}", exc_info=True)
                        else:
                            logger.warning(f"Telegram getUpdates response not OK: {data}")
                            await asyncio.sleep(2.0)
                    else:
                        logger.warning(f"Telegram getUpdates HTTP {resp.status_code}: {resp.text}")
                        await asyncio.sleep(3.0)
                except asyncio.CancelledError:
                    logger.info("Фоновая задача Telegram Long Polling отменена.")
                    break
                except Exception as e:
                    if not self._is_polling:
                        break
                    logger.warning(f"Сетевая ошибка при Telegram Long Polling: {e}. Повтор через 2с...")
                    await asyncio.sleep(2.0)

        logger.info("Telegram Bot Long Polling остановлен.")

    def stop_polling(self):
        """Остановка фонового цикла Long Polling."""
        self._is_polling = False

    def set_binding_callback(self, callback: Callable):
        """Установить асинхронный колбэк при успешной привязке Telegram."""
        self._binding_callback = callback

    async def _notify_binding(self, student_id: str, telegram_id: int, telegram_username: Optional[str]):
        """Оповещение веб-клиентов через SSE AuditBroadcaster о привязке Telegram."""
        if self._binding_callback:
            try:
                res = self._binding_callback(student_id, telegram_id, telegram_username)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error(f"Error in telegram_bot binding callback: {e}")
        else:
            try:
                from backend.main import audit_broadcaster
                await audit_broadcaster.broadcast({
                    "type": "telegram_linked",
                    "student_id": student_id,
                    "telegram_id": telegram_id,
                    "telegram_username": telegram_username,
                })
            except Exception as e:
                logger.error(f"Error in direct audit_broadcaster broadcast: {e}")

    @property
    def is_dev_mode(self) -> bool:
        return self.bot_token in ("", "dev", "test")

    def build_tma_url(self, start_param: Optional[str] = None) -> str:
        """Формирует URL перехода в Telegram Mini App с параметрами темы."""
        base_url = f"{self.public_url}/tma"
        if start_param:
            # Преобразуем алиасы deep linking (pai_<topic_id> -> <topic_id>)
            topic_param = start_param
            if topic_param.startswith("pai_"):
                topic_param = topic_param[4:]
            if topic_param == "week_09":
                topic_param = "week_09_deep_learning"
            else:
                from backend.database import resolve_topic_id
                topic_param = resolve_topic_id(topic_param)
            return f"{base_url}?topic={topic_param}&start_param={start_param}"
        return base_url

    def build_inline_keyboard(self, start_param: Optional[str] = None) -> Dict[str, Any]:
        """Создает инлайн-клавиатуру Telegram с кнопкой запуска Web App (строго HTTPS для Telegram)."""
        tma_url = self.build_tma_url(start_param)
        rows = []
        if tma_url.startswith("https://"):
            rows.append([
                {
                    "text": "🚀 Открыть Themis Mini App",
                    "web_app": {"url": tma_url}
                }
            ])
        rows.append([
            {
                "text": "🛡 О принципах UDL и защите балла",
                "callback_data": "info_udl"
            }
        ])
        return {"inline_keyboard": rows}

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

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> Dict[str, Any]:
        """Ответ на callback_query пользователя через Telegram Bot API."""
        if self.is_dev_mode:
            logger.info(f"[DEV BOT] answer_callback_query: cq_id={callback_query_id}, text={text}")
            return {"ok": True, "result": True}

        api_url = f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery"
        payload: Dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
            payload["show_alert"] = show_alert

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(api_url, json=payload)
                return resp.json()
        except Exception as e:
            logger.error(f"Failed to answer callback query {callback_query_id}: {e}")
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

                # Проверка: является ли start_param одноразовым токеном привязки (One-Time Binding Deep Link)
                is_binding_attempt = False
                if start_param:
                    if start_param.startswith("bind_") or get_telegram_binding_token(start_param) is not None:
                        is_binding_attempt = True

                if is_binding_attempt and start_param:
                    token_rec = get_telegram_binding_token(start_param)
                    if not token_rec or token_rec.get("status") in ("USED", "EXPIRED"):
                        warning_text = (
                            "⚠️ <b>Эта ссылка уже была использована или устарела.</b>\n\n"
                            "Получите новый персональный QR-код в веб-кабинете."
                        )
                        await self.send_message(chat_id, warning_text)
                        return {
                            "ok": True,
                            "action": "binding_rejected",
                            "chat_id": chat_id,
                            "reason": token_rec.get("status") if token_rec else "not_found"
                        }

                    # Токен валиден и находится в статусе PENDING
                    student_id = token_rec["student_id"]
                    user_id = user.get("id") or chat_id
                    raw_user = user.get("username")
                    telegram_username = f"@{raw_user}" if (raw_user and not raw_user.startswith("@")) else raw_user

                    # 1. Привязываем Telegram аккаунт к student_id
                    link_telegram_identity(student_id, user_id, telegram_username)

                    # 2. Сжигаем токен (переводим в USED)
                    mark_binding_token_used(token_rec["token"])

                    # 3. Получаем имя студента
                    identity = get_student_identity(student_id)
                    display_name = (identity.get("display_name") if identity else None) or student_id
                    group_str = "Группа 1"
                    if identity and identity.get("group_id") and identity["group_id"] != "group_1":
                        group_str = identity["group_id"]

                    # 4. Отправляем подтверждение со ссылкой на TMA
                    confirm_text = (
                        f"✅ Вы успешно авторизованы как <b>{display_name} ({group_str})</b>!\n\n"
                        f"Ваш аккаунт Telegram привязан к ведомости. Нажмите кнопку ниже, чтобы открыть сократическую сессию:"
                    )
                    tma_url = f"{self.public_url}/tma"
                    keyboard = None
                    if tma_url.startswith("https://"):
                        keyboard = {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "🚀 Открыть сократическую сессию",
                                        "web_app": {"url": tma_url}
                                    }
                                ]
                            ]
                        }
                    else:
                        confirm_text += (
                            f"\n\n📱 <i>Ссылка для локального веб-клиента:</i> {tma_url}\n"
                            f"<i>(Для запуска Mini App прямо внутри мобильного Telegram подключите HTTPS через Cloudflare tunnel: cloudflared tunnel --url http://127.0.0.1:8000)</i>"
                        )
                    await self.send_message(chat_id, confirm_text, reply_markup=keyboard)

                    # 5. Оповещаем веб-клиент через SSE AuditBroadcaster
                    await self._notify_binding(student_id, user_id, telegram_username)

                    return {
                        "ok": True,
                        "action": "binding_success",
                        "chat_id": chat_id,
                        "student_id": student_id,
                        "telegram_id": user_id,
                        "telegram_username": telegram_username
                    }

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
                    "👋 Чтобы начать или продолжить сократический диалог, нажмите кнопку ниже:"
                )
                keyboard = self.build_inline_keyboard()
                await self.send_message(chat_id, reminder_text, reply_markup=keyboard)
                tma_url = self.build_tma_url()
                return {"ok": True, "action": "fallback_handled", "chat_id": chat_id, "tma_url": tma_url}

        # 2. Обработка callback_query
        callback_query = update.get("callback_query")
        if callback_query:
            cq_id = callback_query.get("id")
            cb_data = callback_query.get("data")
            from_chat = callback_query.get("message", {}).get("chat", {})
            chat_id = from_chat.get("id")

            if cq_id:
                await self.answer_callback_query(cq_id)

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
