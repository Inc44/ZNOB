from __future__ import annotations

from pathlib import Path
from typing import List
from urllib.parse import urlparse

import imgkit
import markdown
import markdownify
import requests
from bs4 import BeautifulSoup, Tag


def convert_html_to_markdown(element: Tag, base_url: str = "") -> str:
	if not element:
		return ""
	for img in element.find_all("img"):
		src = img.get("src", "")
		if base_url and not src.startswith(("http://", "https://")):
			if src.startswith("/"):
				src = base_url + src
			else:
				src = base_url + ("" if base_url.endswith("/") else "/") + src
			img["src"] = src
	html = str(element)
	soup = BeautifulSoup(html, "html.parser")
	for img in soup.find_all("img"):
		src = img.get("src", "")
		alt = img.get("alt", "")
		img.replace_with(f"![{alt}]({src})")
	html = str(soup)
	return markdownify.markdownify(html, escape_underscores=False)


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
		answers_sections = task_card.select(".answers")
		for answers_section in answers_sections:
			quest_title = answers_section.select_one(".quest-title")
			if quest_title:
				title_text = convert_html_to_markdown(quest_title, base_url).strip()
				snippet += f"{title_text}\n\n"
			answers = answers_section.select(".answer")
			for answer in answers:
				marker = (
					answer.select_one(".marker").text.strip()
					if answer.select_one(".marker")
					else ""
				)
				if answer.select_one(".marker"):
					answer.select_one(".marker").extract()
				markdown_answer = convert_html_to_markdown(answer, base_url).strip()
				snippet += f"**{marker}** {markdown_answer}\n\n"
			snippet += "\n"
		markdown_snippets.append(snippet)
	return markdown_snippets


def extract_answers_from_html(html: str) -> List[str]:
	soup = BeautifulSoup(html, "html.parser")
	task_cards = soup.select(".task-card")
	answers_snippets = []
	for task_card in task_cards:
		table = task_card.select_one("table.select-answers-variants")
		if table:
			rows = table.find_all("tr")[1:]
			answers = []
			for row in rows:
				th = row.find("th", class_="r")
				tds = row.find_all("td")
				if th:
					subquestion = th.text.strip()
					for j, td in enumerate(tds):
						if td.find("span", class_="marker ok"):
							letter = chr(ord("А") + j)
							answers.append(f"{subquestion}-{letter}")
				else:
					for j, td in enumerate(tds):
						if td.find("span", class_="marker ok"):
							letter = chr(ord("А") + j)
							answers.append(letter)
							break
			snippet = (
				", ".join(answers)
				if len(answers) > 1
				else answers[0]
				if answers
				else ""
			)
			answers_snippets.append(snippet)
		else:
			answers_snippets.append("")
	return answers_snippets


def convert_markdown_to_png(snippet: str, output_path: Path | str) -> None:
	html = markdown.markdown(snippet, extensions=["tables"])
	html_document = f"""
<!DOCTYPE html>
<html>
<head>
	<style>
		body{{font-family: sans-serif;padding: 1.25rem;background-color: white;}}
		h2{{color: lightseagreen;}}
		strong{{font-weight: bold;}}
		em{{font-style: italic;}}
		table{{border-collapse: collapse;}}
		table,td{{border: 0.0625rem solid black;padding: 0.3125rem;}}
		th{{display: none;}}
	</style>
</head>
<body>{html}</body>
</html>
	"""
	imgkit.from_string(html_document, output_path, options={"width": 512, "quiet": ""})


def prepare_questions(url: str, questions_dir: Path) -> None:
	if url.startswith(("http://", "https://")):
		resp = requests.get(url)
		html = resp.text
	else:
		with open(url, "r", encoding="utf-8") as file:
			html = file.read()
	soup = BeautifulSoup(html, "html.parser")
	base = soup.find("base")
	if base and base.get("href"):
		base_url = base["href"]
	else:
		if url.startswith(("http://", "https://")):
			parsed_url = urlparse(url)
			base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
		else:
			base_url = ""
	markdown_snippets = extract_markdown_from_html(html, base_url=base_url)
	answers_snippets = extract_answers_from_html(html)
	for i, snippet in enumerate(markdown_snippets, 1):
		markdown_question_path = questions_dir / f"{i}.md"
		with markdown_question_path.open("w", encoding="utf-8") as file:
			file.write(snippet)
		image_question_path = questions_dir / f"{i}.png"
		convert_markdown_to_png(snippet, image_question_path)
	answers_path = questions_dir.parent / "answers.md"
	answers_lines = [
		f"{i}) {answer}" for i, answer in enumerate(answers_snippets, 1) if answer
	]
	with answers_path.open("w", encoding="utf-8") as file:
		file.write("\n".join(answers_lines))
