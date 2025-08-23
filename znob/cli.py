from __future__ import annotations

import argparse
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
		)
	else:
		arg_parser.print_help()


if __name__ == "__main__":
	main()
