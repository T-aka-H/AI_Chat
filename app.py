# AI ディベートアプリ - バックエンド
from flask import Flask, request, jsonify, send_from_directory
import requests
import os
from dotenv import load_dotenv
import logging
from flask_cors import CORS
import re

# カスタムログフィルター（APIキーを隠す）
class APIKeyFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'msg'):
            # URLに含まれるAPIキーを隠す
            if isinstance(record.msg, str):
                record.msg = re.sub(r'key=[A-Za-z0-9_-]+', 'key=***HIDDEN***', record.msg)
                # URLエンコードされたAPIキーも隠す
                record.msg = re.sub(r'key%3D[A-Za-z0-9_-]+', 'key%3D***HIDDEN***', record.msg)
            # 引数内のAPIキーを隠す
            if hasattr(record, 'args'):
                record.args = tuple(
                    re.sub(r'key=[A-Za-z0-9_-]+', 'key=***HIDDEN***', str(arg))
                    if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# APIキーフィルターを追加
logger.addFilter(APIKeyFilter())

# サードパーティライブラリのログレベルを調整
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# 環境変数の読み込み
load_dotenv()

# APIキーを環境変数から安全に取得
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.critical('GEMINI_API_KEYが環境変数に設定されていません')
    raise ValueError('GEMINI_API_KEY must be set in environment variables')

app = Flask(__name__)

# CORSの設定
CORS(app, origins="*")

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
        'gemini_configured': bool(GEMINI_API_KEY)  # APIキー自体は公開しない
    })

@app.route('/api/ai-debate', methods=['POST', 'OPTIONS'])
def ai_debate():
    """Gemini AIを使用したディベート応答API"""
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
        
        if not GEMINI_API_KEY:
            logger.error('APIキーが設定されていません')
            return jsonify({'error': 'APIキーが設定されていません'}), 500
        
        # Gemini APIを呼び出し
        response_text = get_gemini_response(prompt, max_tokens)
        
        return jsonify({
            'success': True,
            'response': response_text
        })
        
    except requests.exceptions.Timeout:
        logger.error('Gemini APIリクエストがタイムアウトしました')
        return jsonify({'error': 'AI応答がタイムアウトしました。再度お試しください。'}), 504
    except Exception as e:
        logger.error(f'AIディベートエラー: {str(e)}')
        return jsonify({'error': 'サーバー内部でエラーが発生しました'}), 500

def get_gemini_response(prompt, max_tokens):
    """Gemini APIを使用して応答を取得"""
    try:
        # APIエンドポイントとパラメータを分離
        base_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'
        
        # プロンプトに応じて文字数制限を変更
        if "議論を整理する" in prompt or "分析" in prompt:
            character_limit = 1200
            enhanced_prompt = prompt
        else:
            character_limit = 150
            enhanced_prompt = f"{prompt}\n\n注意: 必ず{character_limit}文字以内で簡潔に回答してください。"
        
        # APIリクエストを送信（APIキーはパラメータとして安全に送信）
        response = requests.post(
            base_url,
            params={'key': GEMINI_API_KEY},  # URLパラメータとして送信
            headers={'Content-Type': 'application/json'},
            json={
                'contents': [{
                    'parts': [{
                        'text': enhanced_prompt
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
            logger.error(f"Gemini API エラー: ステータスコード {response.status_code}")
            raise Exception('Gemini APIからエラーレスポンスを受信しました')
        
        data = response.json()
        
        if 'candidates' not in data or len(data['candidates']) == 0:
            raise Exception('Gemini APIからの応答が予期された形式ではありません')
        
        candidate = data['candidates'][0]
        
        if 'finishReason' in candidate and candidate['finishReason'] == 'SAFETY':
            return "申し訳ございませんが、このトピックについては安全性の観点から応答を生成できません。"
        
        text_content = candidate['content']['parts'][0]['text'].strip()
        
        # 文字数制限に応じて切り詰め（句読点で自然に区切る）
        if character_limit == 150 and len(text_content) > 180:
            # 150文字以内で最後の句読点を探す
            cut_point = 150
            for i in range(min(150, len(text_content)-1), 0, -1):
                if text_content[i] in ['。', '！', '？']:
                    cut_point = i + 1
                    break
            
            # 句読点が見つからなかった場合、読点で区切る
            if cut_point == 150:
                for i in range(min(150, len(text_content)-1), 0, -1):
                    if text_content[i] in ['、', ' ']:
                        cut_point = i
                        break
            
            text_content = text_content[:cut_point].rstrip()
            # 句読点で終わっていない場合は「...」を追加
            if text_content and text_content[-1] not in ['。', '！', '？']:
                text_content += "..."
                
        elif character_limit == 1200 and len(text_content) > 1200:
            # 1200文字以内で最後の句読点を探す
            cut_point = 1200
            for i in range(min(1200, len(text_content)-1), 0, -1):
                if text_content[i] in ['。', '！', '？']:
                    cut_point = i + 1
                    break
            
            text_content = text_content[:cut_point].rstrip()
            # 句読点で終わっていない場合は「...」を追加
            if text_content and text_content[-1] not in ['。', '！', '？']:
                text_content += "..."
        
        # 最低限の文字数を確保
        if len(text_content) < 20:
            logger.warning(f"生成されたテキストが短すぎます: {len(text_content)}文字")
        
        return text_content
        
    except requests.exceptions.Timeout:
        logger.error('Gemini APIリクエストがタイムアウトしました')
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
    
    logger.info('AIディベートアプリを起動します')
    # APIキーの存在確認のみをログに出力（値は出力しない）
    logger.info('環境変数確認 - GEMINI_API_KEY: %s', '設定済み' if GEMINI_API_KEY else '未設定')
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)