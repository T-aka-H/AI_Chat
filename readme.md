# AI ディベートアプリ

AIが様々な視点から議論を展開するインタラクティブなディベートアプリケーションです。

## 機能

- 🎯 任意のトピックについてAIが意見を述べる
- ⚔️ AIが自身の意見に対して反論を展開
- 🔄 継続的な議論の展開（意見→反論→再反論...）
- 📊 ディベートの統計情報表示（ターン数、総文字数）
- 🎨 美しいグラデーションデザインとアニメーション

## 技術スタック

- **フロントエンド**: HTML, CSS, JavaScript（バニラJS）
- **バックエンド**: Python Flask
- **AI**: Google Gemini API
- **スタイリング**: カスタムCSS（グラデーション、アニメーション）

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd ai-debate-app
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example`を`.env`にコピーして、Gemini APIキーを設定します：

```bash
cp .env.example .env
```

`.env`ファイルを編集：
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. アプリケーションの起動

```bash
python app.py
```

ブラウザで`http://localhost:5000`にアクセスしてください。

## 使い方

1. **トピックの入力**: ディベートしたいトピックを入力フィールドに記入
2. **AIの意見を聞く**: 「AIに意見を聞く」ボタンをクリック
3. **反論を聞く**: AIの意見が表示されたら「AIの反論を聞く」ボタンをクリック
4. **議論の継続**: 反論ボタンを押し続けることで議論が深まります
5. **新しいディベート**: 右上の「新しいディベート」ボタンでリセット

## プロジェクト構造

```
ai-debate-app/
├── app.py              # Flaskバックエンド
├── index.html          # メインHTML
├── debate.js           # フロントエンドJavaScript
├── requirements.txt    # Python依存関係
├── .env.example        # 環境変数の例
└── README.md          # このファイル
```

## APIエンドポイント

- `GET /` - メインページ
- `GET /api/health` - ヘルスチェック
- `POST /api/ai-debate` - AI応答を取得

### AI Debate APIリクエスト例

```json
{
  "prompt": "AIは人間の仕事を奪うか？",
  "max_tokens": 400
}
```

## カスタマイズ

### スタイルの変更

`index.html`内の`<style>`セクションでデザインをカスタマイズできます：

- グラデーションカラー
- アニメーション速度
- フォントサイズ
- レイアウト

### AI設定の調整

`app.py`の`get_gemini_response`関数で以下を調整可能：

- `temperature`: 創造性の度合い（0.0〜1.0）
- `maxOutputTokens`: 最大出力トークン数
- `topP`, `topK`: 応答の多様性

## トラブルシューティング

### Gemini APIキーエラー
- `.env`ファイルにAPIキーが正しく設定されているか確認
- APIキーの権限が有効か確認

### 応答が長すぎる場合
- バックエンドで200文字制限を実装済み
- 必要に応じて`app.py`の文字数制限を調整

### CORSエラー
- ローカル開発では`CORS(app, origins="*")`で全オリジンを許可
- 本番環境では適切なオリジンを指定

## デプロイ

### Renderへのデプロイ

1. Renderアカウントを作成
2. 新しいWeb Serviceを作成
3. GitHubリポジトリを接続
4. 環境変数`GEMINI_API_KEY`を設定
5. デプロイを実行

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します！大きな変更の場合は、まずissueを作成して変更内容について議論してください。