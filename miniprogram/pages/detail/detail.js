// pages/detail/detail.js
const app = getApp();

Page({
  data: {
    detail: {},
    taskId: ''
    ,
    isFavorite: false
  },

  onLoad(options) {
    console.log('详情页接收参数：', options);
    if (options.taskId) {
      this.setData({ taskId: options.taskId });
      this.loadDetail(options.taskId);
    } else {
      wx.showToast({
        title: '参数错误',
        icon: 'error',
        complete: () => {
          wx.navigateBack();
        }
      });
    }
  },

  // 加载详情数据
  loadDetail(taskId) {
    wx.showLoading({ title: '加载中...' });
    
    wx.request({
      url: 'https://sakuranightingale.top/api/query-result',
      method: 'GET',
      data: {
        task_id: taskId,
        user_id: app.globalData.user_id
      },
      success: (res) => {
        wx.hideLoading();
        console.log('详情数据：', res.data);
        
        if (res.data.code === 200 && res.data.results && res.data.results.length > 0) {
          const d = res.data.results[0];
          this.setData({
            detail: d,
            isFavorite: !!d.favorite // backend should return this flag
          });
        } else {
          wx.showToast({
            title: '获取详情失败',
            icon: 'error'
          });
        }
      },
      fail: (err) => {
        wx.hideLoading();
        console.error('获取详情失败：', err);
        wx.showToast({
          title: '网络错误',
          icon: 'error'
        });
      }
    });
  },

  // 复制链接
  copyUrl() {
    const url = this.data.detail.url;
    if (url) {
      wx.setClipboardData({
        data: url,
        success: () => {
          wx.showToast({ title: '链接已复制' });
        }
      });
    }
  },

  // 复制摘要
  copySummary() {
    const summary = this.data.detail.summary;
    if (summary) {
      wx.setClipboardData({
        data: summary,
        success: () => {
          wx.showToast({ title: '摘要已复制' });
        }
      });
    }
  },

  // 跳转到原文
  navigateToUrl() {
    const url = this.data.detail.url;
    if (url) {
      // 检查是否是合法URL
      if (url.startsWith('http://') || url.startsWith('https://')) {
        wx.setClipboardData({
          data: url,
          success: () => {
            wx.showModal({
              title: '提示',
              content: '原文链接已复制到剪贴板，请在浏览器中打开',
              showCancel: false,
              confirmText: '知道了'
            });
          }
        });
      } else {
        wx.showToast({
          title: '链接格式错误',
          icon: 'error'
        });
      }
    }
  },

  // 切换收藏状态
  toggleFavorite() {
    const fav = this.data.isFavorite ? 0 : 1;
    const card = this.data.detail;
    const userId = app.globalData.user_id;
    const taskId = card.task_id || card.id;
    
    if (!userId || !taskId) {
      wx.showToast({ title: '数据异常', icon: 'none' });
      return;
    }
    
    wx.request({
      url: 'https://sakuranightingale.top/api/mini/update-status',
      method: 'POST',
      data: {
        user_id: userId,
        task_id: taskId,
        favorite: fav
      },
      success: (res) => {
        console.log('toggleFavorite success:', res);
        this.setData({ isFavorite: !!fav });
        wx.showToast({ title: fav ? '已收藏' : '取消收藏', icon: 'success' });
      },
      fail: (err) => {
        console.error('更新收藏失败', err);
        wx.showToast({ title: '操作失败', icon: 'none' });
      }
    });
  }
});