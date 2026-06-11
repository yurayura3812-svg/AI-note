import gradio as gr
import os
import re
import json
from groq import Groq
from dotenv import load_dotenv
from pydub import AudioSegment
import tempfile

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def clean_transcript(text: str) -> str:
    return re.sub(r'^[、。]+', '', text)


def compress_audio(audio_file: str) -> str:
    audio = AudioSegment.from_file(audio_file)
    audio = audio.set_channels(1).set_frame_rate(16000)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    audio.export(tmp.name, format="mp3", bitrate="32k")
    return tmp.name


def transcribe_audio(audio_file: str) -> str:
    compressed = compress_audio(audio_file)
    try:
        with open(compressed, "rb") as f:
            result = client.audio.transcriptions.create(
                file=(os.path.basename(compressed), f),
                model="whisper-large-v3",
                language="ja",
                response_format="text",
            )
    finally:
        os.remove(compressed)
    return clean_transcript(result)


def generate_note(transcript: str) -> dict:
    prompt = f"""以下の音声テキストから学習ノートを作成してください。
必ず以下のJSON形式で返してください。他の文字は一切含めないでください。

{{
  "summary": "全体の要約（200字程度の自然な日本語）",
  "keywords": [
    {{"word": "用語名", "description": "説明"}},
    {{"word": "用語名", "description": "説明"}}
  ],
  "quiz": [
    {{"question": "問題文", "answer": "答え"}},
    {{"question": "問題文", "answer": "答え"}},
    {{"question": "問題文", "answer": "答え"}}
  ]
}}

テキスト：
{transcript}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "あなたは講義内容から学習ノートを作成するアシスタントです。必ず指定されたJSON形式のみで返答してください。",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1024,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)


def format_keywords(keywords: list) -> str:
    lines = []
    for kw in keywords:
        lines.append(f"**{kw['word']}**\n{kw['description']}")
    return "\n\n".join(lines)


def format_quiz(quiz: list) -> str:
    lines = []
    for i, q in enumerate(quiz, 1):
        lines.append(f"**Q{i}. {q['question']}**\n\n<details><summary>答えを見る</summary>\n\nA. {q['answer']}\n\n</details>")
    return "\n\n---\n\n".join(lines)


def process_input(audio_file, text_input: str):
    transcript = ""
    show_transcript = True

    if text_input and text_input.strip():
        transcript = clean_transcript(text_input)
        show_transcript = False
    elif audio_file is not None:
        if not os.path.exists(audio_file):
            return gr.update(value="エラー: 音声ファイルが見つかりません。", visible=True), "", "", ""
        try:
            transcript = transcribe_audio(audio_file)
        except Exception as e:
            return gr.update(value=f"音声認識エラー: {e}", visible=True), "", "", ""
    else:
        return gr.update(value="音声またはテキストを入力してください。", visible=True), "", "", ""

    try:
        note = generate_note(transcript)
        summary = note.get("summary", "")
        keywords = format_keywords(note.get("keywords", []))
        quiz = format_quiz(note.get("quiz", []))
    except Exception as e:
        return gr.update(value=transcript, visible=show_transcript), f"ノート生成エラー: {e}", "", ""

    return gr.update(value=transcript, visible=show_transcript), summary, keywords, quiz


with gr.Blocks(title="AI学習ノート生成アプリ") as iface:
    gr.Markdown("# AI学習ノート生成アプリ")
    gr.Markdown("音声をアップロードするか、テキストを貼り付けると、要約・キーワード・クイズを自動生成します。")

    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(type="filepath", label="音声を録音またはアップロード")
            text_input = gr.Textbox(lines=8, label="または、テキストを直接貼り付け")
            submit_btn = gr.Button("ノートを生成する", variant="primary")

    transcript_output = gr.Textbox(label="文字起こし結果", lines=5, visible=False)

    with gr.Tabs():
        with gr.Tab("要約"):
            summary_output = gr.Markdown()
        with gr.Tab("キーワード"):
            keywords_output = gr.Markdown()
        with gr.Tab("クイズ"):
            quiz_output = gr.Markdown()

    submit_btn.click(
        fn=process_input,
        inputs=[audio_input, text_input],
        outputs=[transcript_output, summary_output, keywords_output, quiz_output],
    )

iface.launch()