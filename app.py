# AI ディベートアプリ - バックエンド
from flask import Flask, request, jsonify, send_from_directory
import requests
import os
from dotenv import load_dotenv
import logging
from flask_cors import CORS

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)

# CORSの設定
CORS(app, origins="*")

# 環境変数から設定を取得
app.config['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY')

@app.route('/')
def index():
    """メインページを提供"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """静的ファイルを提供"""
    return send_from_directory('.', filename)

@app.route('/api/health')
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Debate App',
        'gemini_configured': bool(app.config['GEMINI_API_KEY'])
    })

@app.route('/api/ai-debate', methods=['POST', 'OPTIONS'])
def ai_debate():
    """Gemini AIを使用したディベート応答API"""
    logger.debug('AIディベートエンドポイントにリクエストを受信')
    
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'リクエストボディが空です'}), 400
        
        prompt = data.get('prompt', '')
        max_tokens = data.get('max_tokens', 400)
        
        if not prompt:
            return jsonify({'error': 'プロンプトが提供されていません'}), 400
        
        if not app.config['GEMINI_API_KEY']:
            return jsonify({'error': 'GEMINI_API_KEY が設定されていません'}), 500
        
        # Gemini APIを呼び出し
        response_text = get_gemini_response(prompt, max_tokens)
        
        return jsonify({
            'success': True,
            'response': response_text
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'AI応答がタイムアウトしました。再度お試しください。'}), 504
    except Exception as e:
        logger.error(f'AIディベートエラー: {str(e)}')
        return jsonify({'error': f'内部エラー: {str(e)}'}), 500

def get_gemini_response(prompt, max_tokens):
    """Gemini APIを使用して応答を取得"""
    logger.info('Gemini APIにリクエスト送信')
    
    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={app.config["GEMINI_API_KEY"]}'
        
        # プロンプトに応じて文字数制限を変更
        if "議論を整理する" in prompt or "分析" in prompt:
            # 要約・分析の場合は文字数制限を緩和
            character_limit = 1000
        else:
            # 通常の意見・反論は150文字
            character_limit = 150
            enhanced_prompt = f"{prompt}\n\n注意: 必ず{character_limit}文字以内で回答してください。"
        
        response = requests.post(
            url,
            headers={
                'Content-Type': 'application/json'
            },
            json={
                'contents': [{
                    'parts': [{
                        'text': enhanced_prompt if character_limit == 150 else prompt
                    }]
                }],
                'generationConfig': {
                    'maxOutputTokens': max_tokens,
                    'temperature': 0.8,
                    'topP': 0.9,
                    'topK': 40
                },
                'safetySettings': [
                    {
                        'category': 'HARM_CATEGORY_HARASSMENT',
                        'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                    },
                    {
                        'category': 'HARM_CATEGORY_HATE_SPEECH',
                        'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                    },
                    {
                        'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
                        'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                    },
                    {
                        'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
                        'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                    }
                ]
            },
            timeout=30
        )
        
        if response.status_code != 200:
            error_msg = f"Gemini API エラー: {response.status_code}"
            logger.error(f"{error_msg}: {response.text}")
            raise Exception(error_msg)
        
        data = response.json()
        
        if 'candidates' not in data or len(data['candidates']) == 0:
            raise Exception('Gemini APIからの応答が予期された形式ではありません')
        
        candidate = data['candidates'][0]
        
        if 'finishReason' in candidate and candidate['finishReason'] == 'SAFETY':
            return "申し訳ございませんが、このトピックについては安全性の観点から応答を生成できません。"
        
        text_content = candidate['content']['parts'][0]['text'].strip()
        
        # 文字数制限に応じて切り詰め
        if character_limit == 150 and len(text_content) > 180:  # 余裕を持って180文字まで
            text_content = text_content[:150] + "..."
        elif character_limit == 1000 and len(text_content) > 1200:  # 余裕を持って1200文字まで
            text_content = text_content[:1000] + "..."
        
        return text_content
        
    except requests.exceptions.Timeout:
        raise Exception('Gemini APIがタイムアウトしました')
    except Exception as e:
        logger.error(f'Gemini API呼び出しエラー: {str(e)}')
        raise

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'エンドポイントが見つかりません'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'内部サーバーエラー: {str(error)}')
    return jsonify({'error': '内部サーバーエラーが発生しました'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']
    
    logger.info(f'AIディベートアプリ起動: ポート {port}')
    logger.info(f'環境変数確認 - GEMINI_API_KEY: {"設定済み" if os.environ.get("GEMINI_API_KEY") else "未設定"}')
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)