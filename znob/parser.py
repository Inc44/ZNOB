from __future__ import annotations

from pathlib import Path
from typing import List
from urllib.parse import urlparse

import imgkit
import markdown
import requests
from bs4 import BeautifulSoup, NavigableString, Tag


def convert_html_to_markdown(element: Tag, base_url: str = "") -> str:
	if not element:
		return ""
	markdown = ""
	for child in element.children:
		if isinstance(child, NavigableString):
			markdown += child
		elif child.name in ["b", "strong"]:
			markdown += "**" + convert_html_to_markdown(child, base_url) + "**"
		elif child.name in ["i", "em"]:
			markdown += "*" + convert_html_to_markdown(child, base_url) + "*"
		elif child.name == "br":
			markdown += "\n"
		elif child.name == "img":
			src = child.get("src", "")
			if src.startswith("/"):
				src = base_url + src
			alt = child.get("alt", "image")
			markdown += f"![{alt}]({src})"
		elif child.name == "table":
			markdown += convert_table_to_markdown(child, base_url) + "\n"
		else:
			markdown += convert_html_to_markdown(child, base_url)
	return markdown


def convert_table_to_markdown(table: Tag, base_url: str) -> str:
	markdown = ""
	rows = table.find_all("tr")
	if not rows:
		return markdown
	headers = rows[0].find_all(["th", "td"])
	header = " | ".join(convert_html_to_markdown(cell, base_url) for cell in headers)
	markdown += header + "\n"
	separator = " | ".join(["---"] * len(headers))
	markdown += separator + "\n"
	for row in rows[1:]:
		cells = row.find_all(["th", "td"])
		row_markdown = " | ".join(
			convert_html_to_markdown(cell, base_url) for cell in cells
		)
		markdown += row_markdown + "\n"
	return markdown


def extract_markdown_from_html(html: str, base_url: str = "") -> List[str]:
	soup = BeautifulSoup(html, "html.parser")
	task_cards = soup.select(".task-card")
	markdown_snippets = []
	for i, task_card in enumerate(task_cards, 1):
		counter = (
			task_card.select_one(".counter").text.strip()
			if task_card.select_one(".counter")
			else f"Завдання {i}"
		)
		question_element = task_card.select_one(".question")
		question = (
			convert_html_to_markdown(question_element, base_url)
			if question_element
			else "Питання відсутнє"
		)
		snippet = f"## {counter}\n\n{question}\n\n"
		answers = task_card.select(".answers .answer")
		for answer in answers:
			marker = (
				answer.select_one(".marker").text.strip()
				if answer.select_one(".marker")
				else ""
			)
			if answer.select_one(".marker"):
				answer.select_one(".marker").extract()
			markdown_answer = convert_html_to_markdown(answer, base_url).strip()
			snippet += f"- **{marker}** {markdown_answer}\n"
		markdown_snippets.append(snippet)
	return markdown_snippets


def convert_markdown_to_png(snippet: str, output_path: Path | str) -> None:
	html = markdown.markdown(snippet, extensions=["tables"])
	html_document = f"""
<!DOCTYPE html>
<html>
<head>
	<style>
		body{{font-family: sans-serif;padding: 1.25rem;background-color: white;}}
		h2{{color: mediumaquamarine;}}
		strong{{font-weight: bold;}}
		em{{font-style: italic;}}
		table{{border-collapse: collapse;}}
		table,th,td{{border: 0.0625rem solid black;padding: 0.3125rem;}}
		img{{max-width: 100%;height: auto;}}
	</style>
</head>
<body>{html}</body>
</html>
    """
	imgkit.from_string(html_document, output_path, options={"width": 720, "quiet": ""})


def prepare_questions(url: str, questions_dir: Path) -> None:
	resp = requests.get(url)
	html = resp.text
	parsed_url = urlparse(url)
	base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
	markdown_snippets = extract_markdown_from_html(html, base_url=base_url)
	for i, snippet in enumerate(markdown_snippets, 1):
		markdown_question_path = questions_dir / f"{i}.md"
		with markdown_question_path.open("w", encoding="utf-8") as file:
			file.write(snippet)
		image_question_path = questions_dir / f"{i}.png"
		convert_markdown_to_png(snippet, image_question_path)
