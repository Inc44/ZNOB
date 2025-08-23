# ZNOB

ZNOB is a multimodal benchmark measuring frontier LLMs' capabilities in passing Ukrainian national exams.

## 🚀 Installation

```bash
conda create -n znob python=3.9 -y # up to 3.13
conda activate znob
git clone https://github.com/Inc44/ZNOB.git
cd ZNOB
pip install -r requirements.txt
```

## 🧾 Configuration

Set environment variable:

```powershell
setx /M OPENROUTER_API_KEY your_api_key
```

For Linux/macOS:

```bash
echo 'export OPENROUTER_API_KEY="your_api_key"' >> ~/.bashrc # or ~/.zshrc
```

Or create a `.env` file or modify /etc/environment:

```
OPENROUTER_API_KEY=your_api_key
```

Check by restarting the terminal and using:

```cmd
echo %OPENROUTER_API_KEY%
```

For Linux/macOS:

```bash
echo $OPENROUTER_API_KEY
```

## 📖 Usage Examples

### Prepare Dataset

```bash
python -m znob.cli -d your_zno_dataset -u your_zno_source
```

### Test LLM

```bash
python -m znob.cli -d your_zno_dataset --model google/gemini-2.5-flash
```

## 🎨 Command-Line Arguments

| Argument               | Description       |
|------------------------|-------------------|
| `-u, --url <url>`      | Dataset source.   |
| `-d, --dataset <path>` | Dataset to test.  |
| `-m, --model <name>`   | AI model to test. |

## 🎯 Motivation

LLMs have made significant progress since November 2024, so I decided to measure their progress and also verify the claims of the [Benchmarking Multimodal Models for Ukrainian Language Understanding Across Academic and Cultural Domains](https://arxiv.org/abs/2411.14647v1) research paper.

## 🐛 Bugs

Not yet found.

## ⛔ Known Limitations

Not yet known.

## 🚧 TODO

Not yet planned.