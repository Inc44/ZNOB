from __future__ import annotations

from pathlib import Path
from typing import List
from urllib.parse import urlparse

import markdown
import markdownify
import requests
from bs4 import BeautifulSoup, Tag
from html2image import Html2Image
from PIL import Image
from PIL.ImageOps import invert


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
		markdown_snippets.append(snippet.strip())
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


def convert_markdown_to_png(
	snippet: str,
	hti: Html2Image,
	questions_dir: Path | str,
	save_as: str,
	stylesheet_href: str = "",
	script_src: str = "",
) -> None:
	html = markdown.markdown(snippet, extensions=["tables"])
	html_document = f"""
<!DOCTYPE html>
<html>
<head>
	<link rel="stylesheet" href="{stylesheet_href}">
	<script src="{script_src}"></script>
	<style>
		body{{background-color: white;}}
		table{{border-collapse: collapse;}}
		table,td{{border: 0.0625rem solid black;padding: 0.3125rem;}}
		th{{display: none;}}
		img{{max-width: 100%;}}
	</style>
</head>
<body>
	{html}
</body>
</html>
	"""
	hti.screenshot(html_str=html_document, save_as=save_as)
	image_question_path = questions_dir / save_as
	image_question = Image.open(image_question_path)
	image_question_bbox = invert(image_question).getbbox()
	if image_question_bbox:
		_, _, right, bottom = image_question_bbox
		image_question = image_question.crop((0, 0, right + 8, bottom + 8))
	image_question.save(image_question_path)


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
	stylesheet_href = ""
	stylesheet = soup.find("link", rel="stylesheet")
	if stylesheet:
		stylesheet_href = stylesheet.get("href", "")
	script_src = ""
	script = soup.find("script", src=True)
	if script:
		script_src = script.get("src", "")
	markdown_snippets = extract_markdown_from_html(html, base_url=base_url)
	answers_snippets = extract_answers_from_html(html)
	hti = Html2Image(
		output_path=str(questions_dir),
		size=(512, 1024),
		disable_logging=True,
	)
	for i, snippet in enumerate(markdown_snippets, 1):
		markdown_question_path = questions_dir / f"{i}.md"
		with markdown_question_path.open("w", encoding="utf-8") as file:
			file.write(snippet)
		convert_markdown_to_png(
			snippet,
			hti,
			questions_dir,
			f"{i}.png",
			stylesheet_href,
			script_src,
		)
	answers_path = questions_dir.parent / "answers.md"
	answers_lines = [
		f"{i}) {answer}" for i, answer in enumerate(answers_snippets, 1) if answer
	]
	with answers_path.open("w", encoding="utf-8") as file:
		file.write("\n".join(answers_lines))
