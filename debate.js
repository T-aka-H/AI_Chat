// AI ディベートアプリ - メインJavaScript
console.log('debate.js読み込み開始');

// グローバル変数
let currentTopic = '';
let debateHistory = [];
let turnCount = 0;
let totalWordCount = 0;
let isProcessing = false;

// ディベートを開始
async function startDebate() {
    const topicInput = document.getElementById('topicInput');
    const topic = topicInput.value.trim();
    
    if (!topic) {
        showNotification('トピックを入力してください', 'error');
        return;
    }
    
    if (isProcessing) {
        showNotification('処理中です。お待ちください。', 'info');
        return;
    }
    
    // 初期化
    currentTopic = topic;
    debateHistory = [];
    turnCount = 0;
    totalWordCount = 0;
    isProcessing = true;
    
    // UI更新
    document.getElementById('topicDisplay').textContent = `トピック: ${topic}`;
    document.getElementById('debateContainer').style.display = 'block';
    document.getElementById('debateContent').innerHTML = '';
    document.getElementById('counterBtn').style.display = 'none';
    document.getElementById('statsContainer').style.display = 'none';
    document.getElementById('startBtn').disabled = true;
    showLoading(true);
    
    try {
        // 最初の意見を取得
        const opinion = await getAIOpinion(topic, true);
        
        if (opinion) {
            addDebateEntry(opinion, 'opinion', 1);
            debateHistory.push({
                type: 'opinion',
                content: opinion,
                turn: 1
            });
            
            turnCount = 1;
            totalWordCount = opinion.length;
            updateStats();
            
            // 反論ボタンを表示
            document.getElementById('counterBtn').style.display = 'inline-block';
            document.getElementById('statsContainer').style.display = 'flex';
        }
    } catch (error) {
        console.error('ディベート開始エラー:', error);
        showNotification('エラーが発生しました: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        document.getElementById('startBtn').disabled = false;
        showLoading(false);
    }
}

// 反論を取得
async function getCounterArgument() {
    if (isProcessing) {
        showNotification('処理中です。お待ちください。', 'info');
        return;
    }
    
    if (debateHistory.length === 0) {
        showNotification('まずトピックについて意見を聞いてください', 'error');
        return;
    }
    
    isProcessing = true;
    document.getElementById('counterBtn').disabled = true;
    showLoading(true);
    
    try {
        // 最後の発言を取得
        const lastStatement = debateHistory[debateHistory.length - 1];
        const isCounterArgument = lastStatement.type === 'counter';
        
        // 反論を取得
        const counterArgument = await getAICounterArgument(
            currentTopic, 
            lastStatement.content,
            isCounterArgument
        );
        
        if (counterArgument) {
            turnCount++;
            const entryType = isCounterArgument ? 'opinion' : 'counter';
            
            addDebateEntry(counterArgument, entryType, turnCount);
            debateHistory.push({
                type: entryType,
                content: counterArgument,
                turn: turnCount
            });
            
            totalWordCount += counterArgument.length;
            updateStats();
        }
    } catch (error) {
        console.error('反論取得エラー:', error);
        showNotification('エラーが発生しました: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        document.getElementById('counterBtn').disabled = false;
        showLoading(false);
    }
}

// AIから意見を取得
async function getAIOpinion(topic, isInitial = true) {
    const prompt = isInitial
        ? `次のトピックについて、あなたの意見を200文字程度で述べてください。論理的で説得力のある意見を提示してください。\n\nトピック: ${topic}`
        : `次のトピックについて、前回とは異なる視点から意見を200文字程度で述べてください。\n\nトピック: ${topic}`;
    
    try {
        const response = await fetch('https://meal-tracker-2-jyq6.onrender.com/api/ai-debate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                max_tokens: 400
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'AI意見の取得に失敗しました');
        }
        
        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error('AI意見取得エラー:', error);
        throw error;
    }
}

// AIから反論を取得
async function getAICounterArgument(topic, previousStatement, isCounterToCounter = false) {
    const prompt = isCounterToCounter
        ? `次のトピックに関する議論で、相手の反論に対してさらに反論してください。200文字程度で論理的に反駁してください。\n\nトピック: ${topic}\n\n相手の反論:\n${previousStatement}`
        : `次のトピックに関する意見に対して、反対の立場から反論してください。200文字程度で論理的に反駁してください。\n\nトピック: ${topic}\n\n相手の意見:\n${previousStatement}`;
    
    try {
        const response = await fetch('https://meal-tracker-2-jyq6.onrender.com/api/ai-debate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                max_tokens: 400
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'AI反論の取得に失敗しました');
        }
        
        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error('AI反論取得エラー:', error);
        throw error;
    }
}

// ディベートエントリーをUIに追加
function addDebateEntry(content, type, turn) {
    const debateContent = document.getElementById('debateContent');
    const entryDiv = document.createElement('div');
    entryDiv.className = `debate-entry ${type}`;
    
    const emoji = type === 'opinion' ? '💭' : '⚔️';
    const label = type === 'opinion' ? '意見' : '反論';
    
    entryDiv.innerHTML = `
        <div class="debate-header">
            <div class="debate-label">
                ${emoji} ${label}
            </div>
            <div class="debate-number">
                ターン ${turn}
            </div>
        </div>
        <div class="debate-content">
            ${content}
        </div>
    `;
    
    debateContent.appendChild(entryDiv);
    
    // 新しいエントリーにスクロール
    entryDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

// 統計情報を更新
function updateStats() {
    document.getElementById('turnCount').textContent = turnCount;
    document.getElementById('wordCount').textContent = totalWordCount;
}

// ディベートをリセット
function resetDebate() {
    currentTopic = '';
    debateHistory = [];
    turnCount = 0;
    totalWordCount = 0;
    isProcessing = false;
    
    document.getElementById('topicInput').value = '';
    document.getElementById('debateContainer').style.display = 'none';
    document.getElementById('debateContent').innerHTML = '';
    document.getElementById('counterBtn').style.display = 'none';
    document.getElementById('statsContainer').style.display = 'none';
    document.getElementById('startBtn').disabled = false;
    
    showNotification('新しいディベートを開始できます', 'success');
}

// ローディング表示の制御
function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = show ? 'inline-block' : 'none';
    }
}

// 通知の表示
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        max-width: 400px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    `;
    
    const colors = {
        success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        error: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
        info: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
    };
    
    notification.style.background = colors[type] || colors.info;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// CSS アニメーションを追加
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 初期化処理
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI ディベートアプリ初期化完了');
    
    // エンターキーでの送信に対応
    const topicInput = document.getElementById('topicInput');
    if (topicInput) {
        topicInput.focus();
    }
});

console.log('debate.js読み込み完了');