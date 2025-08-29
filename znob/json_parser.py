from __future__ import annotations

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
	if question.get("answerGroups"):
		for group in question["answerGroups"]:
			quest_title = group.get("quest-title", "")
			if quest_title:
				html += '<div class="answers">\n'
				html += f'<div class="quest-title"><i>{quest_title}</i></div>\n'
			else:
				html += '<div class="answers">\n'
			for answer in group["answers"]:
				html += '<div class="answer">\n'
				html += f'<span class="marker">{answer["marker"]}</span>{answer["answer"]}\n'
				html += "</div>\n"
			html += "</div>\n"
	html += '<div class="description">\n'
	html += f'Вид завдання: <a href="{question["help"]}" target="_blank">{question["type_text"]}</a>\n'
	html += "</div>\n"
	html += "</div>\n"
	return html


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
	return snippet.strip()


def prepare_questions_from_json(json_path: str, questions_dir: Path) -> None:
	pass
