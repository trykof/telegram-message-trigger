from telegram_message_trigger.text_format import strip_html_preview


def test_strip_html_preview_removes_tg_emoji_tag() -> None:
    assert strip_html_preview('<tg-emoji emoji-id="123">⭐</tg-emoji> привет') == "⭐ привет"


def test_strip_html_preview_unescapes_entities() -> None:
    assert strip_html_preview("&lt;3 &amp; &quot;ok&quot;") == '<3 & "ok"'


def test_strip_html_preview_plain_text_unchanged() -> None:
    assert strip_html_preview("просто текст") == "просто текст"
