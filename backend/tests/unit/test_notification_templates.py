"""Unit tests for the notification-template rendering helper (doc §17)."""
from app.services.notifications import _render_template_field


class TestRenderTemplateField:
    def test_uses_fallback_when_no_template(self):
        assert _render_template_field(None, {"x": "1"}, "fallback text") == "fallback text"

    def test_uses_fallback_when_template_is_empty_string(self):
        assert _render_template_field("", {"x": "1"}, "fallback text") == "fallback text"

    def test_renders_template_when_all_placeholders_resolve(self):
        result = _render_template_field("Hello {name}!", {"name": "World"}, "fallback")
        assert result == "Hello World!"

    def test_falls_back_on_missing_placeholder(self):
        # Template references a var the caller never passed - stale/typo'd
        # placeholder must not raise or leak a literal "{missing}" to a user.
        result = _render_template_field("Hi {missing}", {"name": "World"}, "fallback text")
        assert result == "fallback text"

    def test_template_with_no_placeholders_is_used_verbatim(self):
        result = _render_template_field("A fully static custom message.", {}, "fallback")
        assert result == "A fully static custom message."
