"""Tests del extractor de texto, headings y enlaces del HTML de Google Docs."""

from __future__ import annotations

from blog_auditor.loaders.html_extract import extract_text_and_links

_PRICING_HREF = "https://www.google.com/url?q=https://teilurtalent.com/pricing&amp;sa=D"
_ARTICLE_HREF = "https://www.google.com/url?q=https://teilurtalent.com/insights/toptal-cost&amp;sa=D"
_GLASSDOOR_HREF = "https://www.google.com/url?q=https://glassdoor.com/salaries&amp;sa=D"

GDOC_HTML = f"""
<html><head><style>.c0 {{ color: #000; }}</style></head><body>
<h1 class="c1">How to Hire DevOps Engineers</h1>
<p class="c2">DevOps hiring is hard. See our
<a href="{_PRICING_HREF}">pricing page</a> for details.</p>
<h2>Step by step</h2>
<p>Read also <a href="{_ARTICLE_HREF}">this article</a>
and an external source <a href="{_GLASSDOOR_HREF}">Glassdoor</a>.</p>
</body></html>
"""


def test_extracts_headings_as_markdown() -> None:
    text, _ = extract_text_and_links(GDOC_HTML)

    assert "# How to Hire DevOps Engineers" in text
    assert "## Step by step" in text


def test_strips_style_and_script_content() -> None:
    text, _ = extract_text_and_links(GDOC_HTML)

    assert "color: #000" not in text
    assert ".c0" not in text


def test_collects_links_with_anchor_text() -> None:
    _, links = extract_text_and_links(GDOC_HTML)

    assert ("pricing page", "https://teilurtalent.com/pricing") in links
    assert ("this article", "https://teilurtalent.com/insights/toptal-cost") in links
    assert ("Glassdoor", "https://glassdoor.com/salaries") in links


def test_unwraps_google_redirect_urls() -> None:
    _, links = extract_text_and_links(GDOC_HTML)
    urls = [url for _, url in links]

    assert all("google.com/url" not in url for url in urls)


def test_handles_html_without_links() -> None:
    text, links = extract_text_and_links("<html><body><p>Solo texto.</p></body></html>")

    assert "Solo texto." in text
    assert links == []
