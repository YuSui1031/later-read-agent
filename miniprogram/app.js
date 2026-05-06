App({
  globalData: {
    user_id: '',
    openid: ''
  },
  
  onLaunch() {
    // 检查本地是否有已绑定的user_id
    const savedUserId = wx.getStorageSync('user_id');
    if (savedUserId) {
      // 已有绑定，直接跳转到explore
      this.globalData.user_id = savedUserId;
      wx.reLaunch({ url: '/pages/explore/explore' });
    } else {
      // 没有绑定，跳转到bind页面
      wx.reLaunch({ url: '/pages/bind/bind' });
    }
  }
});
