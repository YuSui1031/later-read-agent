// pages/bind/bind.js
Page({
  data: {
    // 绑定状态
    isBound: false,
    userId: '',
    userIdShort: '',
    
    // 扫码相关
    scene: '',
    sessionId: '',
    
    // 调试模式
    debug: true
  },

  onLoad(options) {
    console.log('绑定页面加载，参数：', options);
    
    // 检查本地是否已有用户ID
    const savedUserId = wx.getStorageSync('user_id');
    if (savedUserId) {
      console.log('已有用户ID，直接进入探索页面:', savedUserId);
      wx.reLaunch({ url: '/pages/explore/explore' });
      return;
    }
    
    // 检查是否有scene参数（从小程序码进入）
    if (options.scene) {
      // 通过二维码进入，自动绑定
      this.setData({ scene: decodeURIComponent(options.scene) });
      this.processScene(options.scene);
    }
    // 没有scene参数，不需要任何操作，等待用户去插件端扫码
  },

  // 处理scene参数（自动绑定流程）
  processScene(scene) {
    try {
      // 解析session参数
      const params = {};
      const sceneStr = decodeURIComponent(scene);
      const pairs = sceneStr.split('&');
      
      for (const pair of pairs) {
        const [key, value] = pair.split('=');
        if (key && value) {
          params[key] = value;
        }
      }
      
      const sessionId = params.session;
      if (!sessionId) {
        console.error('scene参数中没有session');
        return;
      }
      
      this.setData({ sessionId });
      console.log('解析到Session ID:', sessionId);
      
      // 自动调用绑定
      this.doBind(sessionId);
      
    } catch (error) {
      console.error('解析scene参数失败：', error);
    }
  },

  // 执行绑定操作（小程序端主导）
  doBind(sessionId) {
    if (!sessionId) {
      wx.showToast({ title: 'Session ID无效', icon: 'none' });
      return;
    }
    
    wx.showLoading({ title: '绑定中...' });
    
    // 步骤1：先获取用户ID
    this.getUserIdByLogin()
      .then(userId => {
        console.log('获取到用户ID:', userId);
        
        // 步骤2：绑定session
        return this.bindSession(sessionId, userId);
      })
      .then(result => {
        wx.hideLoading();
        console.log('绑定成功:', result);
        
        // 保存用户ID到本地存储
        wx.setStorageSync('user_id', result.user_id);
        
        // 更新页面数据
        this.setData({
          isBound: true,
          userId: result.user_id,
          userIdShort: this.shortenUserId(result.user_id)
        });
        
        // 显示成功提示
        wx.showToast({ 
          title: '绑定成功', 
          icon: 'success',
          duration: 1500
        });
        
        // 延迟跳转，让用户看到提示
        setTimeout(() => {
          wx.reLaunch({ url: '/pages/explore/explore' });
        }, 1500);
      })
      .catch(err => {
        wx.hideLoading();
        console.error('绑定失败:', err);
        wx.showToast({ title: err.message || '绑定失败', icon: 'none' });
      });
  },

  // 通过登录获取用户ID（小程序端主导）
  getUserIdByLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (loginRes) => {
          if (!loginRes.code) {
            reject(new Error('获取登录code失败'));
            return;
          }
          
          console.log('获取到登录code:', loginRes.code);
          
          // 调用登录接口获取用户ID
          wx.request({
            url: 'https://sakuranightingale.top/api/mini/login',
            method: 'POST',
            header: { 'content-type': 'application/json' },
            data: { code: loginRes.code },
            success: (res) => {
              console.log('登录响应:', res.data);
              if (res.statusCode === 200 && res.data && res.data.code === 200) {
                resolve(res.data.user_id);
              } else {
                reject(new Error(res.data?.detail || '获取用户ID失败'));
              }
            },
            fail: (err) => {
              reject(new Error('网络错误'));
            }
          });
        },
        fail: () => {
          reject(new Error('微信登录失败'));
        }
      });
    });
  },

  // 绑定session（小程序端主导）
  bindSession(sessionId, userId) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: 'https://sakuranightingale.top/api/mini/scene-bind',
        method: 'POST',
        header: { 'content-type': 'application/json' },
        data: {
          scene: `session=${sessionId}`,
          user_id: userId  // 小程序端主导：直接传入user_id
        },
        success: (res) => {
          console.log('绑定响应:', res.data);
          if (res.statusCode === 200 && res.data && res.data.code === 200) {
            resolve(res.data);
          } else {
            reject(new Error(res.data?.detail || '绑定session失败'));
          }
        },
        fail: (err) => {
          reject(new Error('网络错误'));
        }
      });
    });
  },

  // 手动输入Session ID
  manualBind() {
    wx.showModal({
      title: '手动绑定',
      content: '请输入插件中显示的Session ID',
      editable: true,
      placeholderText: '输入Session ID',
      success: (res) => {
        if (res.confirm && res.content) {
          const sessionId = res.content.trim();
          this.setData({ sessionId });
          this.doBind(sessionId);
        }
      }
    });
  },

  // 扫描二维码
  scanQRCode() {
    wx.scanCode({
      onlyFromCamera: true,
      scanType: ['qrCode'],
      success: (res) => {
        console.log('扫码结果:', res);
        
        if (res.result) {
          // 尝试解析scene参数
          if (res.result.includes('session=')) {
            this.processScene(res.result);
          } else {
            // 尝试作为sessionId直接使用
            this.doBind(res.result);
          }
        }
      },
      fail: (err) => {
        console.error('扫码失败:', err);
        wx.showToast({ title: '扫码失败', icon: 'none' });
      }
    });
  },

  // 前往探索页面
  goToExplore() {
    wx.reLaunch({ url: '/pages/explore/explore' });
  },

  // 返回
  goBack() {
    wx.reLaunch({ url: '/pages/explore/explore' });
  },

  // 测试登录（仅开发环境使用）
  testLogin() {
    wx.showLoading({ title: '测试登录中...' });
    
    wx.request({
      url: 'https://sakuranightingale.top/api/mini/login',
      method: 'POST',
      header: { 'content-type': 'application/json' },
      data: { code: 'test-code' },
      success: (res) => {
        wx.hideLoading();
        console.log('测试登录响应:', res);
        
        if (res.statusCode === 200 && res.data && res.data.code === 200) {
          const userId = res.data.user_id;
          wx.setStorageSync('user_id', userId);
          
          this.setData({
            isBound: true,
            userId: userId,
            userIdShort: this.shortenUserId(userId)
          });
          
          wx.showToast({ title: '测试登录成功', icon: 'success' });
          setTimeout(() => wx.reLaunch({ url: '/pages/explore/explore' }), 1000);
        } else {
          wx.showToast({ title: res.data?.detail || '测试模式未开启', icon: 'none' });
        }
      },
      fail: (err) => {
        wx.hideLoading();
        console.error('测试登录失败:', err);
        wx.showToast({ title: '网络错误', icon: 'none' });
      }
    });
  },

  // 工具函数
  shortenUserId(userId) {
    if (!userId) return '';
    if (userId.length <= 12) return userId;
    return userId.substring(0, 8) + '...' + userId.substring(userId.length - 4);
  }
});
