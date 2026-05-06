// pages/history/history.js
Page({
  data: {
    results: []
  },

  onShow() {
    this.loadHistory();
  },

  getUserId() {
    let userId = wx.getStorageSync('user_id');
    if (!userId) {
      const app = getApp();
      if (app && app.globalData) {
        userId = app.globalData.user_id;
      }
    }
    return userId;
  },

  loadHistory() {
    const userId = this.getUserId();
    if (!userId) {
      this.setData({ results: [] });
      return;
    }
    wx.request({
      url: `https://sakuranightingale.top/api/mini/results?user_id=${userId}&limit=10`,
      success: (res) => {
        if (res.data.code === 200) {
          this.setData({ results: res.data.results || [] });
        }
      },
      fail: (err) => {
        console.error('获取历史失败', err);
      }
    });
  },

  navigateToDetail(e) {
    const taskId = e.currentTarget.dataset.taskid;
    if (!taskId) {
      wx.showToast({ title: '数据异常', icon: 'error' });
      return;
    }
    const url = `/pages/detail/detail?taskId=${encodeURIComponent(taskId)}`;
    wx.navigateTo({ url });
  },

  clearHistory() {
    const userId = this.getUserId();
    if (userId) {
      wx.request({
        url: 'https://sakuranightingale.top/api/mini/clear-history',
        method: 'POST',
        data: { user_id: userId },
        success: () => {
          this.setData({ results: [] });
          wx.showToast({ title: '历史记录已清空', icon: 'success' });
        },
        fail: (err) => {
          console.error('清空历史失败', err);
          wx.showToast({ title: '清空失败', icon: 'none' });
        }
      });
    }
  }
});
