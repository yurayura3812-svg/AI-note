---
title: AI-note
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "6.17.3"
app_file: app.py
pinned: false
---
# AI学習ノート生成アプリ

**デモ：** https://huggingface.co/spaces/yusei68/AI-note

---

## 概要

講義の音声またはテキストを入力すると、AIが自動で学習ノートを生成するWebアプリです。
要約・重要キーワード・理解度確認クイズをタブ形式で表示します。
既存の音声要約アプリに「学習用途への特化」という差別化を加え、個人で設計・実装・デプロイまで行いました。

---

## 技術的なポイント

### 1. 音声認識
- Groq Whisper API（whisper-large-v3）で高精度な日本語文字起こしを実現
- pydubで音声を圧縮（モノラル化・16000Hz・32kbps）してからAPIに送信することで、大容量ファイルのサイズ制限（25MB）に対応

### 2. 学習ノート生成
- LLMへの指示をJSON形式で返すよう設計し、要約・キーワード・クイズを1回のAPIコールで同時生成
- クイズの答えはHTMLのdetailsタグで折りたたみ表示し、学習効果を考慮したUI設計

### 3. CI/CDパイプライン
- GitHub ActionsでGitHubへのpushをトリガーにHugging Face Spacesへ自動デプロイ
- HuggingFace TokenをGitHub Secretsに格納し、APIキーをコードに含めない設計

---

## 使用技術

| 分類 | 技術 |
|------|------|
| フロントエンド | Gradio |
| 音声認識 | Groq Whisper API（whisper-large-v3） |
| ノート生成 | Groq LLM API（llama-3.3-70b-versatile） |
| 音声処理 | pydub |
| デプロイ | Hugging Face Spaces |
| CI/CD | GitHub Actions |

---

## 技術選定理由

| 技術 | 選定理由 |
|------|----------|
| Groq API | 無料枠があり個人開発に導入しやすい。入力データが学習に使用されないためプライバシーに配慮できる。推論速度が速くレスポンス体験を損なわない |
| Gradio | PythonのみでUIを構築できる。Hugging Face Spacesとの親和性が高く無料デプロイが容易 |
| pydub | ffmpegに依存せずPythonのみで音声圧縮が可能。デプロイ環境での依存関係トラブルを回避できる |
| GitHub Actions | pushをトリガーにした自動デプロイを実現し、手動アップロードの手間を排除 |

---

## 開発中のトラブルと対応

| トラブル | 原因 | 対応 |
|----------|------|------|
| 音声認識エラー（413） | Groq APIのファイルサイズ制限（25MB）超過 | pydubで音声を圧縮してから送信するよう変更 |
| ノート生成エラー | llama-3.1-70bが廃止済み | llama-3.3-70bに変更 |
| pyaudioopインストール失敗 | Python 3.13非対応 | requirements.txtから削除（gradioが自動でaudioop-ltsを導入） |
| HuggingFaceへのpush失敗 | Space作成時の自動コミットと競合 | --force pushに変更 |
| GitHub Actionsのpush失敗（shallow update） | actionsがリポジトリを浅くクローンしていた | fetch-depth: 0を追加して全履歴を取得 |
| GROQ_API_KEY not found | HuggingFace SpacesにSecretを未設定 | SpacesのSettings→Secretsに追加 |

---

## システム構成

    音声ファイル or テキスト入力
        ↓
    （音声の場合）pydubで圧縮 → Groq Whisper APIで文字起こし
        ↓
    Groq LLM APIでノート生成（要約・キーワード・クイズをJSON形式で取得）
        ↓
    タブ形式で表示（要約 / キーワード / クイズ）

---

## 今後の展望

- PDFや動画URLからの入力対応
- ノートのダウンロード機能（Markdown / PDF出力）
- 長時間講義への対応（チャンク分割処理）

---

## ローカル実行

**1. リポジトリをクローン**

    git clone https://github.com/yurayura3812-svg/AI-note.git
    cd AI-note
    pip install -r requirements.txt

**2. `.env` を作成**

    GROQ_API_KEY=your_groq_api_key

**3. 起動**

    python app.py
