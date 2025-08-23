from __future__ import annotations

import base64
import concurrent.futures
import os
from pathlib import Path
from typing import List

import requests


def ask(markdown: str, image: Path | None, model: str) -> str:
	openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
	if not openrouter_api_key:
		raise RuntimeError("OPENROUTER_API_KEY environment variable is required.")
	headers = {
		"Authorization": f"Bearer {openrouter_api_key}",
		"Accept": "application/json",
	}
	content = [{"type": "text", "text": markdown}]
	if image and image.exists():
		with image.open("rb") as image_file:
			encoded = base64.b64encode(image_file.read()).decode("utf-8")
		content.append(
			{
				"type": "image_url",
				"image_url": {"url": f"data:image/png;base64,{encoded}"},
			}
		)
	payload = {
		"model": model,
		"messages": [
			{
				"role": "user",
				"content": content,
			}
		],
	}
	resp = requests.post(
		"https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload
	)
	resp.raise_for_status()
	return resp.json()["choices"][0]["message"]["content"]


def process_question(
	i: int, questions_dir: Path, responses_dir: Path, model: str
) -> str:
	markdown_question_path = questions_dir / f"{i}.md"
	image_question_path = questions_dir / f"{i}.png"
	response_path = (
		responses_dir / f"{i}_{model.replace("/", "_").replace(":", "_")}.md"
	)
	with markdown_question_path.open("r", encoding="utf-8") as file:
		markdown_question = file.read()
	response = ask(markdown_question, image_question_path, model)
	with response_path.open("w", encoding="utf-8") as file:
		file.write(response)
	return response


def process_questions(
	questions_dir: Path,
	responses_dir: Path,
	combined_responses_dir: Path,
	summary_dir: Path,
	model: str,
) -> None:
	model_filename = model.replace("/", "_").replace(":", "_")
	tasks = []
	i = 1
	while True:
		markdown_question_path = questions_dir / f"{i}.md"
		image_question_path = questions_dir / f"{i}.png"
		if not (markdown_question_path.exists() and image_question_path.exists()):
			break
		response_path = (
			responses_dir / f"{i}_{model.replace("/", "_").replace(":", "_")}.md"
		)
		if not response_path.exists():
			tasks.append(i)
		i += 1
	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = {
			executor.submit(process_question, j, questions_dir, responses_dir, model): j
			for j in tasks
		}
		for future in concurrent.futures.as_completed(futures):
			future.result()
	responses: List[str] = []
	for j in range(1, i):
		response_path = (
			responses_dir / f"{j}_{model.replace("/", "_").replace(":", "_")}.md"
		)
		with response_path.open("r", encoding="utf-8") as file:
			responses.append(file.read())
	combined_responses = ""
	for j, response in enumerate(responses, 1):
		combined_responses += f"## Завдання {j}\n\n{response}\n\n"
	combined_responses_path = combined_responses_dir / f"{model_filename}.md"
	with combined_responses_path.open("w", encoding="utf-8") as file:
		file.write(combined_responses)
	summary_prompt = f"Підсумуй відповіді у форматі:\n\nномер питання) відповідь або номер питання) 1. відповідь, 2. відповідь, 3. відповідь, ...\n\n{combined_responses}"
	summary = ask(summary_prompt, None, model)
	summary_path = summary_dir / f"{model_filename}.md"
	with summary_path.open("w", encoding="utf-8") as file:
		file.write(summary)
