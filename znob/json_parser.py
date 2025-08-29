from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup
from html2image import Html2Image
from PIL import Image
from PIL.ImageOps import invert

from .parser import convert_html_to_markdown


def convert_question_to_html(question: dict) -> str:
	html = f'<div id="{question["id"]}" class="task-card">\n'
	html += f'<div class="counter">{question["counter"]}</div>\n'
	html += '<div class="question">\n'
	html += question["question"] + "\n"
	html += "</div>\n"
	answers_sections = question.get("answersSections", [])
	if answers_sections:
		for answer_section in answers_sections:
			quest_title = answer_section.get("quest-title", "")
			if quest_title:
				html += '<div class="answers">\n'
				html += f'<div class="quest-title"><i>{quest_title}</i></div>\n'
			else:
				html += '<div class="answers">\n'
			answers = answer_section["answers"]
			for answer in answers:
				marker = answer["marker"]
				html += '<div class="answer">\n'
				html += f'<span class="marker">{marker}</span>{answer["answer"]}\n'
				html += "</div>\n"
			html += "</div>\n"
	html += '<div class="description">\n'
	html += f'Вид завдання: <a href="{question["help"]}" target="_blank">{question["type_text"]}</a>\n'
	html += "</div>\n"
	html += "</div>\n"
	return html


def sanitize_markdown_images(snippet: str) -> str:
	snippet = re.sub(
		r"\!\[([^\]]*)\]\(([^)]+)\)",
		lambda match: f"![{match.group(1)}]({Path(match.group(2)).name})",
		snippet,
	)
	return snippet


def convert_question_to_markdown(question: dict, base_url: str) -> str:
	counter = question["counter"]
	soup = BeautifulSoup(question["question"], "html.parser")
	markdown_question = convert_html_to_markdown(soup, base_url).strip()
	snippet = f"## {counter}\n\n{markdown_question}\n\n"
	answers_sections = question.get("answersSections", [])
	if answers_sections:
		for answer_section in answers_sections:
			quest_title = answer_section.get("quest-title", "")
			if quest_title:
				soup = BeautifulSoup(f"<i>{quest_title}</i>", "html.parser")
				title_text = convert_html_to_markdown(soup, base_url).strip()
				snippet += f"{title_text}\n\n"
			answers = answer_section["answers"]
			for answer in answers:
				marker = answer["marker"]
				soup = BeautifulSoup(answer["answer"], "html.parser")
				markdown_answer = convert_html_to_markdown(soup, base_url).strip()
				snippet += f"**{marker}** {markdown_answer}\n\n"
	type_text = f"Вид завдання: {question["type_text"]}"
	snippet += type_text
	snippet = sanitize_markdown_images(snippet)
	return snippet.strip()


def extract_answer_from_question(question: dict) -> str:
	correct = question.get("correct")
	if isinstance(correct, str):
		return correct
	elif isinstance(correct, list):
		return ", ".join(correct)
	elif isinstance(correct, dict):
		answers = [
			f"{marker}-{correct[marker]}"
			for marker in sorted(correct, key=lambda x: int(x) if x.isdigit() else x)
		]
		return ", ".join(answers)
	else:
		return ""


def convert_question_to_png(
	question: dict,
	hti: Html2Image,
	questions_dir: Path | str,
	save_as: str,
	stylesheet_href: str,
	script_src: str,
	base_url: str,
) -> None:
	html = convert_question_to_html(question)
	html_document = f"""
<!DOCTYPE html>
<html>
<head>
	<base href="{base_url}">
	<link rel="stylesheet" href="{stylesheet_href}">
	<script src="{script_src}"></script>
	<style>
		body{{background-color: white;}}
		td{{min-width: 32px;}}
	</style>
</head>
<body>
	<br>
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


def prepare_questions_from_json(json_path: str, questions_dir: Path) -> None:
	with open(json_path, "r", encoding="utf-8") as file:
		data = json.load(file)
	base_url = data.get("base_url", "")
	stylesheet_href = data.get("stylesheet_url", "")
	script_src = data.get("mathjax_url", "")
	questions = data.get("questions", [])
	answers_snippets: List[str] = []
	hti = Html2Image(
		output_path=str(questions_dir),
		size=(512, 1024),
		disable_logging=True,
	)
	for i, question in enumerate(questions, 1):
		snippet = convert_question_to_markdown(question, base_url)
		markdown_question_path = questions_dir / f"{i}.md"
		with markdown_question_path.open("w", encoding="utf-8") as file:
			file.write(snippet)
		convert_question_to_png(
			question,
			hti,
			questions_dir,
			f"{i}.png",
			stylesheet_href,
			script_src,
			base_url,
		)
		answer_snippet = extract_answer_from_question(question)
		answers_snippets.append(answer_snippet)
	answers_path = questions_dir.parent / "answers.md"
	answers_lines = [
		f"{i}) {answer}" for i, answer in enumerate(answers_snippets, 1) if answer
	]
	with answers_path.open("w", encoding="utf-8") as file:
		file.write("\n".join(answers_lines))
