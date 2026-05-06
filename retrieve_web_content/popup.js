// 认证工具模块
const AuthUtils = {
    // 获取用户ID（从本地存储或绑定流程）
    async getUserId() {
        let userId = localStorage.getItem("web_analyzer_user_id");
        if (userId) {
            return userId;
        }
        
        // 没有用户ID，需要绑定
        return null;
    },

    // 创建绑定会话
    async createBindSession() {
        try {
            const res = await fetch("https://sakuranightingale.top/api/auth/session", {
                method: 'POST',
                mode: 'cors',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: '创建会话失败' }));
                throw new Error(errorData.detail || '创建会话失败');
            }
            
            const data = await res.json();
            return {
                session_id: data.session_id,
                qr_url: data.qr_url,
                qrcode_data: data.qrcode_data,
                expires_at: data.expires_at,
                is_test: data.is_test || false,
                test_user_id: data.test_user_id || null
            };
        } catch (e) {
            console.error('创建绑定会话失败', e);
            throw e;
        }
    },

    // 检查绑定状态
    async checkBindStatus(session_id) {
        try {
            const res = await fetch(`https://sakuranightingale.top/api/auth/session/${session_id}`, {
                method: 'GET',
                mode: 'cors'
            });
            
            if (res.status === 404 || res.status === 410) {
                return { expired: true };
            }
            
            const data = await res.json();
            return data;
        } catch (e) {
            console.error('检查绑定状态失败', e);
            return { error: e.message };
        }
    },

    // 获取小程序码图片URL
    getMiniprogramQrcodeUrl(session_id) {
        return `https://sakuranightingale.top/api/auth/qr/${session_id}`;
    },

    // 获取小程序码信息（JSON格式）
    async getQrcodeInfo(session_id) {
        try {
            const res = await fetch(`https://sakuranightingale.top/api/auth/qr-info/${session_id}`, {
                method: 'GET',
                mode: 'cors'
            });
            
            if (!res.ok) {
                throw new Error('获取小程序码信息失败');
            }
            
            return await res.json();
        } catch (e) {
            console.error('获取小程序码信息失败', e);
            return null;
        }
    },

    // 保存用户ID
    saveUserId(userId) {
        localStorage.setItem("web_analyzer_user_id", userId);
    },

    // 清除用户ID（退出登录）
    clearUserId() {
        localStorage.removeItem("web_analyzer_user_id");
    }
};

// 工具函数模块
const Utils = {
    // 压缩文本内容
    compressContent(content) {
        content = content.replace(/\s+/g, ' ').trim();
        if (content.length > 5000) {
            content = content.substring(0, 5000) + "[内容过长，已截断]";
        }
        return content;
    }
};

// 提取模块
const Extractor = {
    // 提取单个标签页内容
    async extractTabContent(tabId) {
        try {
            const extractResult = await chrome.scripting.executeScript({
                target: { tabId: tabId },
                func: () => {
                    // 移除script、style标签
                    const removeTags = ['script', 'style', 'noscript', 'iframe'];
                    removeTags.forEach(tag => {
                        const elements = document.getElementsByTagName(tag);
                        Array.from(elements).forEach(el => el.remove());
                    });

                    // 提取正文（优先取article、main，其次body）
                    let text = '';
                    const article = document.querySelector('article') || document.querySelector('main') || document.body;
                    if (article) {
                        text = article.textContent || '';
                    }

                    // 清理多余空格和换行
                    text = text.replace(/\s+/g, ' ').trim();
                    return text || document.title + ' - 无正文内容';
                }
            });
            return extractResult[0].result ? Utils.compressContent(extractResult[0].result) : null;
        } catch (e) {
            console.error(`提取内容失败 ${tabId}：`, e);
            return null;
        }
    }
};

// 提交模块
const Submitter = {
    // 提交标签页数据到后端
    async submitTabData(tab, content, userId) {
        const response = await fetch("https://sakuranightingale.top/api/plugin/submit", {
            method: 'POST',
            mode: 'cors',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                url: tab.url,
                title: tab.title,
                user_id: userId,
                batch_id: `batch_${Date.now()}` // 批量任务ID，用于标识同一批提取
            })
        });

        if (!response.ok) {
            throw new Error(`提交失败：${response.status}`);
        }

        return await response.json();
    }
};

// UI 管理模块
const UIManager = {
    resultDiv: document.getElementById('result'),
    allTabs: [],
    selectedTabIds: new Set(),

    // 初始化事件绑定
    init() {
        // 绑定历史记录按钮
        document.getElementById('historyBtn').addEventListener('click', this.showHistory.bind(this));

        // 绑定单个提取按钮
        document.getElementById('extractBtn').addEventListener('click', this.extractCurrentTab.bind(this));

        // 绑定批量提取按钮
        document.getElementById('batchBtn').addEventListener('click', this.showBatchTabList.bind(this));

        // 绑定全选按钮
        document.getElementById('selectAllBtn').addEventListener('click', this.toggleSelectAll.bind(this));

        // 绑定取消批量按钮
        document.getElementById('cancelBatchBtn').addEventListener('click', this.hideBatchUI.bind(this));

        // 绑定确认批量提取按钮
        document.getElementById('confirmBatchBtn').addEventListener('click', this.startBatchExtract.bind(this));
    },

    // 显示历史记录
    showHistory() {
        if (!App.isBound) {
            this.resultDiv.textContent = "请先使用小程序扫码绑定用户";
            return;
        }
        
        // 检查是否已有打开的历史记录窗口
        if (this.historyWindow && !this.historyWindow.closed) {
            // 已有窗口，获得焦点
            this.historyWindow.focus();
            this.resultDiv.textContent = "历史记录页面已打开";
            return;
        }
        
        this.resultDiv.textContent = "正在打开历史记录页面...";
        this.historyWindow = window.open(`https://sakuranightingale.top/history?user_id=${App.userId}`, '_blank');
        setTimeout(() => {
            this.resultDiv.textContent = "历史记录页面已打开，可在新标签页查看～";
        }, 1000);
    },

    // 提取当前标签页
    async extractCurrentTab() {
        if (!App.isBound) {
            this.resultDiv.textContent = "请先使用小程序扫码绑定用户";
            return;
        }
        
        this.resultDiv.textContent = "正在提取页面内容...";
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            const content = await Extractor.extractTabContent(tab.id);
            if (content) {
                const res = await Submitter.submitTabData(tab, content, App.userId);
                this.resultDiv.textContent = `✅ 提交成功！
任务ID：${res.task_id}
👉 可点击「查看历史记录」查看分析进度
💡 无需等待，你可以继续浏览网页～`;
            } else {
                this.resultDiv.textContent = "❌ 未提取到页面内容，请换个网页试试";
            }
        } catch (e) {
            this.resultDiv.textContent = `❌ 提取出错：${e.message}`;
        }
    },

    // 显示批量标签页列表
    async showBatchTabList() {
        try {
            this.allTabs = await chrome.tabs.query({ currentWindow: true });
            const tabList = document.getElementById('tabList');
            const tabCount = document.getElementById('tabCount');

            tabCount.textContent = this.allTabs.length;
            tabList.innerHTML = '';
            this.selectedTabIds.clear();

            this.allTabs.forEach(tab => {
                if (tab.url.startsWith('chrome://') || tab.url.startsWith('about:')) return;

                const tabItem = document.createElement('div');
                tabItem.className = 'tab-item';
                tabItem.innerHTML = `
                    <input type="checkbox" id="tab_${tab.id}" data-tab-id="${tab.id}">
                    <div>
                        <div class="tab-title">${tab.title || '无标题'}</div>
                        <div class="tab-url">${tab.url}</div>
                    </div>
                `;

                const checkbox = tabItem.querySelector('input');
                checkbox.addEventListener('change', (e) => {
                    const tabId = parseInt(e.target.dataset.tabId);
                    if (e.target.checked) {
                        this.selectedTabIds.add(tabId);
                    } else {
                        this.selectedTabIds.delete(tabId);
                    }
                });

                tabList.appendChild(tabItem);
            });

            document.getElementById('batchContainer').style.display = 'block';
            document.getElementById('batchActions').style.display = 'flex';
            this.resultDiv.textContent = "请勾选需要提取的标签页，然后点击确认～";
        } catch (e) {
            this.resultDiv.textContent = `❌ 获取标签页失败：${e.message}`;
        }
    },

    // 全选/取消全选
    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.tab-item input');
        const isAllSelected = this.selectedTabIds.size === checkboxes.length;

        checkboxes.forEach(checkbox => {
            checkbox.checked = !isAllSelected;
            const tabId = parseInt(checkbox.dataset.tabId);
            if (!isAllSelected) {
                this.selectedTabIds.add(tabId);
            } else {
                this.selectedTabIds.delete(tabId);
            }
        });
    },

    // 隐藏批量UI
    hideBatchUI() {
        document.getElementById('batchContainer').style.display = 'none';
        document.getElementById('batchActions').style.display = 'none';
        document.getElementById('progressBar').style.display = 'none';
        this.resultDiv.textContent = "批量提取已结束，可继续使用其他功能～";
    },

    // 开始批量提取
    async startBatchExtract() {
        if (!App.isBound) {
            this.resultDiv.textContent = "请先使用小程序扫码绑定用户";
            return;
        }
        
        if (this.selectedTabIds.size === 0) {
            this.resultDiv.textContent = "❌ 请至少勾选一个标签页";
            return;
        }

        const selectedTabs = this.allTabs.filter(tab => this.selectedTabIds.has(tab.id));
        const total = selectedTabs.length;
        
        // 显示进度条
        document.getElementById('batchActions').style.display = 'none';
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        progressBar.style.display = 'block';
        
        // 控制并发数
        const MAX_CONCURRENT = 3;
        let completed = 0;
        let successCount = 0;
        
        // 创建任务队列
        const processQueue = async (queue, concurrent) => {
            const results = [];
            const executing = [];
            
            for (const [index, tab] of queue.entries()) {
                const p = (async () => {
                    try {
                        const content = await Extractor.extractTabContent(tab.id);
                        if (content) {
                            await Submitter.submitTabData(tab, content, App.userId);
                            successCount++;
                        }
                        
                        // 更新进度
                        completed++;
                        const progress = Math.floor((completed / total) * 100);
                        
                        // 通过requestAnimationFrame避免频繁DOM操作
                        requestAnimationFrame(() => {
                            progressFill.style.width = `${progress}%`;
                            this.resultDiv.textContent = 
                                `批量提取中：${completed}/${total}（${progress}%）`;
                        });
                        
                        return { success: true, tab };
                    } catch (e) {
                        completed++;
                        console.error(`提取失败 ${tab.id}：`, e);
                        return { success: false, tab, error: e };
                    }
                })();
                
                results.push(p);
                
                // 控制并发
                if (concurrent <= queue.length) {
                    const e = p.then(() => executing.splice(executing.indexOf(e), 1));
                    executing.push(e);
                    if (executing.length >= concurrent) {
                        await Promise.race(executing);
                    }
                }
            }
            
            return Promise.allSettled(results);
        };
        
        this.resultDiv.textContent = `开始批量提取 ${total} 个标签页...`;
        await processQueue(selectedTabs, MAX_CONCURRENT);
        
        this.resultDiv.textContent = 
            `共处理 ${total} 个标签页，成功 ${successCount} 个\n` +
            `点击「查看历史记录」查看所有分析结果`;
        
        setTimeout(() => this.hideBatchUI(), 3000);
    }
};

// 主应用模块
const App = {
    userId: null,
    isBound: false,
    currentSession: null,
    pollInterval: null,
    countdownInterval: null,
    isLoggingOut: false,  // 退出登录标志，防止测试模式自动绑定
    expiredShown: false,  // 过期提示已显示标志

    async init() {
        // 尝试获取用户ID
        try {
            this.userId = await AuthUtils.getUserId();
            if (this.userId) {
                this.isBound = true;
                this.showMainUI();
            } else {
                // 用户未绑定，显示绑定界面
                await this.showBindUI();
            }
        } catch (e) {
            console.error('初始化失败', e);
            this.showError('插件初始化失败，请检查网络或后端服务');
        }
    },

    async showBindUI() {
        // 创建绑定会话
        try {
            const session = await AuthUtils.createBindSession();
            this.currentSession = session;
            this.expiredShown = false;  // 重置过期提示标志
            
            // 测试模式：直接使用测试用户ID（除非是退出登录后）
            if (session.is_test && session.test_user_id && !this.isLoggingOut) {
                console.log('测试模式：自动绑定测试用户');
                this.userId = session.test_user_id;
                this.isBound = true;
                AuthUtils.saveUserId(this.userId);
                this.showMainUI();
                return;
            }
            this.isLoggingOut = false;  // 重置退出登录标志
            
            // 计算剩余时间
            const remainingTime = Math.max(0, session.expires_at - Math.floor(Date.now() / 1000));
            const minutes = Math.floor(remainingTime / 60);
            const seconds = remainingTime % 60;
            
            // 显示微信小程序码绑定界面
            const html = `
                <div style="text-align: center; padding: 20px;">
                    <h3 style="margin-bottom: 20px;">请使用微信小程序扫码绑定</h3>
                    
                    <!-- 会话信息 -->
                    <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef;">
                        <div style="font-family: monospace; font-size: 11px; word-break: break-all; color: #6c757d; margin-bottom: 8px;">
                            会话ID: ${session.session_id}
                        </div>
                        <div style="color: #495057; font-size: 12px; margin-bottom: 5px;">
                            有效期: ${new Date(session.expires_at * 1000).toLocaleTimeString()}
                        </div>
                        <div style="color: #dc3545; font-size: 12px; font-weight: 500;">
                            剩余时间: ${minutes}分${seconds}秒
                        </div>
                    </div>
                    
                    <!-- 操作步骤 -->
                    <div style="text-align: left; margin: 20px 0; padding: 15px; background: #e8f4fd; border-radius: 8px;">
                        <p style="margin: 8px 0; font-size: 13px; color: #0d6efd;">
                            <strong>📱 绑定步骤：</strong>
                        </p>
                        <p style="margin: 8px 0; font-size: 13px; color: #495057;">
                            1. 打开微信，搜索并进入「AI网页分析」小程序
                        </p>
                        <p style="margin: 8px 0; font-size: 13px; color: #495057;">
                            2. 点击小程序中的「扫码绑定」按钮
                        </p>
                        <p style="margin: 8px 0; font-size: 13px; color: #495057;">
                            3. 扫描下方的小程序码完成绑定
                        </p>
                    </div>
                    
                    <!-- 微信小程序码 -->
                    <div style="margin: 25px 0; padding: 20px; background: white; border: 1px solid #dee2e6; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <div style="margin-bottom: 15px; font-size: 14px; color: #495057;">
                            <strong>微信小程序码</strong>
                        </div>
                        <img id="miniprogramQrcode" 
                             src="${session.qrcode_data.base64 || AuthUtils.getMiniprogramQrcodeUrl(session.session_id)}" 
                             alt="微信小程序码"
                             style="width: 200px; height: 200px; border: 1px solid #e9ecef; border-radius: 4px;"
                             onerror="this.src='${AuthUtils.getMiniprogramQrcodeUrl(session.session_id)}'">
                        </img>
                        <div style="margin-top: 15px; font-size: 12px; color: #6c757d;">
                            使用微信扫描此码，自动跳转小程序完成绑定
                        </div>
                        ${session.qrcode_data.is_mock ? '<div style="margin-top: 10px; font-size: 11px; color: #fd7e14; font-style: italic;">（开发模式：模拟小程序码）</div>' : ''}
                    </div>
                    
                    <!-- 状态提示 -->
                    <div id="bindStatus" style="margin: 15px 0; padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; display: none;">
                        <div style="font-size: 13px; color: #856404;">
                            <span id="statusText">正在等待绑定...</span>
                        </div>
                    </div>
                    
                    <!-- 操作按钮 -->
                    <div style="margin-top: 25px; display: flex; gap: 10px; justify-content: center;">
                        <button id="checkBindBtn" style="padding: 10px 20px; background: #0d6efd; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; flex: 1;">
                            🔄 检查绑定状态
                        </button>
                        <button id="refreshQrBtn" style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; flex: 1;">
                            🔁 刷新二维码
                        </button>
                    </div>
                    
                    <!-- 倒计时 -->
                    <div id="countdown" style="margin-top: 15px; font-size: 12px; color: #6c757d;">
                        二维码将在 <span id="countdownTime">${minutes}:${seconds.toString().padStart(2, '0')}</span> 后过期
                    </div>
                </div>
            `;
            document.getElementById('result').innerHTML = html;
            
            // 绑定按钮事件
            document.getElementById('checkBindBtn').addEventListener('click', () => this.checkBindStatus());
            document.getElementById('refreshQrBtn').addEventListener('click', () => this.refreshQRCode());
            
            // 开始轮询绑定状态和倒计时
            this.startPolling();
            this.startCountdown();
            
        } catch (e) {
            this.showError(`创建绑定会话失败: ${e.message}`);
        }
    },

    async checkBindStatus() {
        if (!this.currentSession) return;
        
        try {
            const status = await AuthUtils.checkBindStatus(this.currentSession.session_id);
            
            if (status.expired) {
                this.showError('会话已过期，请刷新二维码');
                this.stopPolling();
                this.stopCountdown();
                return;
            }
            
            if (status.is_bound && status.user_id) {
                // 绑定成功
                this.userId = status.user_id;
                this.isBound = true;
                AuthUtils.saveUserId(this.userId);
                this.stopPolling();
                this.stopCountdown();
                this.showMainUI();
            } else {
                // 显示绑定状态提示
                this.showBindStatus('正在等待小程序扫码绑定...');
            }
        } catch (e) {
            console.error('检查绑定状态失败', e);
            this.showBindStatus('检查绑定状态失败，请重试');
        }
    },
    
    showBindStatus(message) {
        const statusDiv = document.getElementById('bindStatus');
        const statusText = document.getElementById('statusText');
        if (statusDiv && statusText) {
            statusDiv.style.display = 'block';
            statusText.textContent = message;
        }
    },

    async refreshQRCode() {
        this.stopPolling();
        this.stopCountdown();
        await this.showBindUI();
    },

    startPolling() {
        // 每5秒检查一次绑定状态
        this.pollInterval = setInterval(() => {
            this.checkBindStatus();
        }, 5000);
    },

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    },
    
    startCountdown() {
        if (!this.currentSession) return;
        
        this.countdownInterval = setInterval(() => {
            this.updateCountdown();
        }, 1000);
    },
    
    stopCountdown() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
    },
    
    updateCountdown() {
        if (!this.currentSession) return;
        
        const countdownElement = document.getElementById('countdownTime');
        if (!countdownElement) return;
        
        const now = Math.floor(Date.now() / 1000);
        const remainingTime = Math.max(0, this.currentSession.expires_at - now);
        
        if (remainingTime <= 0) {
            // 会话已过期
            countdownElement.textContent = '00:00';
            // 只显示一次过期提示
            if (!this.expiredShown) {
                this.expiredShown = true;
                this.showError('二维码已过期，请刷新二维码');
            }
            this.stopPolling();
            this.stopCountdown();
            return;
        }
        
        const minutes = Math.floor(remainingTime / 60);
        const seconds = remainingTime % 60;
        countdownElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        // 最后30秒显示红色警告
        if (remainingTime <= 30) {
            countdownElement.style.color = '#dc3545';
            countdownElement.style.fontWeight = 'bold';
        }
    },

    showMainUI() {
        // 显示主界面
        const html = `
            <div style="text-align: center; padding: 20px;">
                <div style="margin-bottom: 20px; padding: 15px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px;">
                    <div style="color: #155724; font-size: 14px; font-weight: 500;">
                        ✅ 已绑定用户：${this.userId ? this.userId.substring(0, 8) + '...' : '未知用户'}
                    </div>
                </div>
                <button id="logoutBtn" style="padding: 8px 16px; background: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; border-radius: 6px; cursor: pointer; font-size: 13px;">
                    退出登录
                </button>
            </div>
        `;
        document.getElementById('result').innerHTML = html;
        
        // 绑定退出登录按钮
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.logout();
        });
        
        // 初始化UI管理器
        UIManager.init();
    },
    
    logout() {
        this.userId = null;
        this.isBound = false;
        this.currentSession = null;
        this.isLoggingOut = true;  // 设置退出登录标志，防止测试模式自动绑定
        AuthUtils.clearUserId();
        this.stopPolling();
        this.stopCountdown();
        this.showBindUI();
    },

    showError(message) {
        const html = `
            <div style="text-align: center; padding: 20px;">
                <div style="margin-bottom: 15px; padding: 15px; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px;">
                    <div style="color: #721c24; font-size: 14px; font-weight: 500;">
                        ❌ ${message}
                    </div>
                </div>
                <button id="retryBtn" style="padding: 10px 20px; background: #0d6efd; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                    重试
                </button>
            </div>
        `;
        document.getElementById('result').innerHTML = html;
        
        document.getElementById('retryBtn').addEventListener('click', () => {
            this.init();
        });
        
        this.stopPolling();
        this.stopCountdown();
    }
};

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});