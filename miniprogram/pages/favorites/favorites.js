// pages/favorites/favorites.js
Page({
  data: {
    favorites: []
  },

  onShow() {
    this.loadFavorites();
  },

  getUserId() {
    return wx.getStorageSync('user_id') || '';
  },

  loadFavorites() {
    const userId = this.getUserId();
    if (!userId) {
      this.setData({ favorites: [] });
      return;
    }
    
    wx.request({
      url: `https://sakuranightingale.top/api/mini/results?user_id=${userId}&status=favorite`,
      success: (res) => {
        if (res.data.code === 200) {
          this.setData({ favorites: res.data.results || [] });
        }
      },
      fail: (err) => {
        console.error('获取收藏失败', err);
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

  removeFavorite(e) {
    const index = e.currentTarget.dataset.index;
    const favorites = [...this.data.favorites];
    const removed = favorites.splice(index, 1)[0];
    
    this.setData({ favorites });
    
    if (removed) {
      wx.request({
        url: 'https://sakuranightingale.top/api/mini/update-status',
        method: 'POST',
        data: {
          user_id: this.getUserId(),
          task_id: removed.task_id || removed.id,
          favorite: 0
        }
      });
    }
    wx.showToast({ title: '已移除', icon: 'success' });
  }
});
