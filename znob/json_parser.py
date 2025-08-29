from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup

from .parser import convert_html_to_markdown


def convert_question_to_html(question: dict) -> str:
	html = f'<div id="{question["id"]}" class="task-card">\n'
	html += f'<div class="counter">{question["counter"]}</div>\n'
	html += '<div class="question">\n'
	for paragraph in question["question"]:
		html += f"<p>{paragraph}</p>\n"
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
	markdown_question = ""
	for paragraph in question["question"]:
		soup = BeautifulSoup(paragraph, "html.parser")
		markdown_question += convert_html_to_markdown(soup, base_url) + "\n\n"
	markdown_question = markdown_question.strip()
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


def prepare_questions_from_json(json_path: str, questions_dir: Path) -> None:
	pass
