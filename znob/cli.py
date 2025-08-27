from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .checker import process_questions
from .parser import prepare_questions


def main() -> None:
	arg_parser = argparse.ArgumentParser(
		description=(
			"ZNOB is a multimodal benchmark measuring frontier "
			"LLMs' capabilities in passing Ukrainian national exams."
		)
	)
	arg_parser.add_argument(
		"-u",
		"--url",
		help="Dataset source.",
	)
	arg_parser.add_argument(
		"-d",
		"--dataset",
		required=True,
		help="Dataset to test.",
	)
	arg_parser.add_argument(
		"-m",
		"--model",
		help="AI model to test.",
	)
	arg_parser.add_argument(
		"-r",
		"--reset",
		help="Reset outputs.",
	)
	arg_parser.add_argument(
		"--no-text",
		action="store_true",
		help="Send only image, no text.",
	)
	arg_parser.add_argument(
		"--no-image",
		action="store_true",
		help="Send only text, no image.",
	)
	arg_parser.add_argument(
		"--necessary-image-only",
		action="store_true",
		help="Send image only if necessary.",
	)
	args = arg_parser.parse_args()
	questions_dir = Path(args.dataset) / "questions"
	responses_dir = Path(args.dataset) / "responses"
	combined_responses_dir = Path(args.dataset) / "combined_responses"
	summary_dir = Path(args.dataset) / "summary"
	for output_dir in [
		questions_dir,
		responses_dir,
		combined_responses_dir,
		summary_dir,
	]:
		output_dir.mkdir(parents=True, exist_ok=True)
	if args.reset:
		outputs = {output.strip() for output in args.reset.split(",") if output.strip()}
		if "all" in outputs:
			outputs = {"questions", "responses", "combined_responses", "summaries"}
		output_dirs = {
			"questions": questions_dir,
			"responses": responses_dir,
			"combined_responses": combined_responses_dir,
			"summary": summary_dir,
		}
		for output in outputs:
			output_dir = output_dirs[output]
			if output_dir.exists():
				shutil.rmtree(output_dir)
		return
	if args.url:
		prepare_questions(args.url, questions_dir)
	elif args.dataset:
		if not args.model:
			raise ValueError("A model is required.")
		process_questions(
			questions_dir,
			responses_dir,
			combined_responses_dir,
			summary_dir,
			args.model,
			args.no_text,
			args.no_image,
			args.necessary_image_only,
		)
	else:
		arg_parser.print_help()


if __name__ == "__main__":
	main()
