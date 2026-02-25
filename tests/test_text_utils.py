"""Tests for src/utils/text_utils.py."""
from src.utils.text_utils import extract_html_text, strip_markdown_fences


class TestStripMarkdownFences:
    def test_json_fences(self):
        text = '```json\n{"key": "value"}\n```'
        assert strip_markdown_fences(text) == '{"key": "value"}\n'

    def test_plain_fences(self):
        text = "```\nhello world\n```"
        assert strip_markdown_fences(text) == "hello world\n"

    def test_no_fences(self):
        text = '{"key": "value"}'
        assert strip_markdown_fences(text) == '{"key": "value"}'

    def test_empty_string(self):
        assert strip_markdown_fences("") == ""

    def test_trailing_newline(self):
        text = '```json\n{"key": "value"}\n```\n'
        assert strip_markdown_fences(text) == '{"key": "value"}\n'

    def test_multiline_content(self):
        text = '```json\n{\n  "a": 1,\n  "b": 2\n}\n```'
        result = strip_markdown_fences(text)
        assert '"a": 1' in result
        assert '"b": 2' in result
        assert "```" not in result


class TestExtractHtmlText:
    def test_strips_script_tags(self):
        html = "<html><body><p>Hello</p><script>alert('x')</script></body></html>"
        result = extract_html_text(html)
        assert "Hello" in result
        assert "alert" not in result

    def test_strips_style_tags(self):
        html = "<html><body><style>.x{color:red}</style><p>Content</p></body></html>"
        result = extract_html_text(html)
        assert "Content" in result
        assert "color" not in result

    def test_strips_nav_footer_header_aside(self):
        html = (
            "<html><body>"
            "<nav>Navigation</nav>"
            "<header>Header</header>"
            "<main><p>Main content</p></main>"
            "<aside>Sidebar</aside>"
            "<footer>Footer</footer>"
            "</body></html>"
        )
        result = extract_html_text(html)
        assert "Main content" in result
        assert "Navigation" not in result
        assert "Header" not in result
        assert "Sidebar" not in result
        assert "Footer" not in result

    def test_plain_text_in_body(self):
        html = "<html><body><p>Simple text</p></body></html>"
        result = extract_html_text(html)
        assert "Simple text" in result

    def test_nested_tags(self):
        html = "<html><body><div><p>Nested <strong>bold</strong> text</p></div></body></html>"
        result = extract_html_text(html)
        assert "Nested" in result
        assert "bold" in result
        assert "text" in result
