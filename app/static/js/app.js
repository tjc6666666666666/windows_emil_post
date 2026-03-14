/**
 * Email Server - 全局JavaScript
 */

// 显示消息提示
function showMessage(message, type = 'info') {
    // 移除已存在的消息
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // 创建新消息
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    document.body.appendChild(messageDiv);
    
    // 3秒后自动消失
    setTimeout(() => {
        messageDiv.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => {
            messageDiv.remove();
        }, 300);
    }, 3000);
}

// 检查登录状态
function checkAuth() {
    const token = localStorage.getItem('token');
    const protectedPages = ['/dashboard', '/compose', '/inbox'];
    const currentPath = window.location.pathname;
    
    if (protectedPages.includes(currentPath) && !token) {
        showMessage('请先登录', 'error');
        setTimeout(() => {
            window.location.href = '/login';
        }, 1000);
    }
}

// 退出登录
function logout() {
    localStorage.removeItem('token');
    showMessage('已退出登录', 'success');
    setTimeout(() => {
        window.location.href = '/';
    }, 1000);
}

// 获取认证头
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// API请求封装
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('token');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };
    
    if (options.body && typeof options.body === 'object') {
        options.body = JSON.stringify(options.body);
    }
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '请求失败');
        }
        
        return data;
    } catch (error) {
        showMessage(error.message, 'error');
        throw error;
    }
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 自动填充回复邮件信息
    const replyTo = localStorage.getItem('replyTo');
    const replySubject = localStorage.getItem('replySubject');
    
    if (replyTo && document.getElementById('to')) {
        document.getElementById('to').value = replyTo;
        localStorage.removeItem('replyTo');
    }
    
    if (replySubject && document.getElementById('subject')) {
        document.getElementById('subject').value = replySubject;
        localStorage.removeItem('replySubject');
    }
});
