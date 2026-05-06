Page({
  data: {
    cards: [],
    currentIndex: 0,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0,
    showLeftHint: false,
    showRightHint: false,
    cardAnimation: [],
    showLoginBtn: false,
    noMore: false,
    isRefreshing: false
  },

  onLoad() {
    this.initPage();
  },

  onShow() {
    // 每次显示页面时重新检查登录状态
    this.initPage();
  },

  onPullDownRefresh() {
    this.refreshData();
  },

  // 初始化页面
  initPage() {
    const userId = this.getUserId();
    console.log('initPage - userId:', userId);
    
    if (!userId) {
      this.setData({ 
        showLoginBtn: true,
        cards: []
      });
      return;
    }
    
    this.setData({ showLoginBtn: false });
    this.loadCards();
  },

  // 获取用户ID - 优先从 localStorage 获取
  getUserId() {
    return wx.getStorageSync('user_id') || '';
  },

  // 刷新数据
  refreshData() {
    if (this.data.isRefreshing) return;
    
    this.setData({ isRefreshing: true });
    
    const userId = this.getUserId();
    if (!userId) {
      this.setData({ isRefreshing: false });
      wx.stopPullDownRefresh();
      return;
    }

    wx.request({
      url: `https://sakuranightingale.top/api/mini/results?user_id=${userId}&status=unread`,
      success: (res) => {
        if (res.data.code === 200) {
          const results = res.data.results || [];
          this.setData({
            cards: results,
            noMore: results.length === 0,
            cardAnimation: []
          });
        }
      },
      fail: (err) => {
        console.error('刷新数据失败', err);
      },
      complete: () => {
        this.setData({ isRefreshing: false });
        wx.stopPullDownRefresh();
      }
    });
  },

  // 跳转到绑定页面
  goToBind() {
    wx.navigateTo({
      url: '/pages/bind/bind'
    });
  },

  // 触摸开始
  onTouchStart(e) {
    const touch = e.touches[0];
    this.setData({
      startX: touch.pageX,
      startY: touch.pageY,
      offsetX: 0,
      offsetY: 0
    });
  },

  // 触摸移动
  onTouchMove(e) {
    const touch = e.touches[0];
    const offsetX = touch.pageX - this.data.startX;
    const offsetY = touch.pageY - this.data.startY;
    
    this.setData({
      offsetX,
      offsetY,
      showLeftHint: offsetY < -30,
      showRightHint: offsetX > 30
    });
  },

  // 触摸结束
  onTouchEnd(e) {
    const { offsetX, offsetY } = this.data;
    
    if (offsetY < -50) {
      // 上滑 - 不感兴趣
      this.swipeUp();
    } else if (offsetX > 50) {
      // 右滑 - 收藏
      this.swipeRight();
    } else {
      // 回弹
      this.resetPosition();
    }
  },

  // 上滑卡片
  swipeUp() {
    const card = this.data.cards[0];
    if (card) {
      this.markAsRead(card);
    }

    const animation = wx.createAnimation({
      duration: 300,
      timingFunction: 'ease-out'
    });
    
    animation.translateY(-1000).opacity(0).step();
    
    const cardAnimation = [...this.data.cardAnimation];
    cardAnimation[0] = animation.export();
    
    this.setData({ cardAnimation });
    
    setTimeout(() => {
      this.nextCard();
    }, 300);
  },

  // 右滑收藏
  swipeRight() {
    const card = this.data.cards[0];
    if (card) {
      this.addToFavorite(card);
    }

    const animation = wx.createAnimation({
      duration: 300,
      timingFunction: 'ease-out'
    });
    
    animation.translateX(500).opacity(0).step();
    
    const cardAnimation = [...this.data.cardAnimation];
    cardAnimation[0] = animation.export();
    
    this.setData({ cardAnimation });
    
    setTimeout(() => {
      this.nextCard();
    }, 300);
  },

  // 下一张卡片
  nextCard() {
    const cards = [...this.data.cards];
    cards.shift();
    
    this.setData({
      cards,
      cardAnimation: [],
      showLeftHint: false,
      showRightHint: false,
      noMore: cards.length === 0
    });
  },

  // 标记为已读
  markAsRead(card) {
    // 保存到本地历史
    const history = wx.getStorageSync('history') || [];
    const existing = history.findIndex(h => h.id === card.id);
    if (existing > -1) {
      history.splice(existing, 1);
    }
    history.unshift({
      ...card,
      viewedAt: new Date().toLocaleString()
    });
    wx.setStorageSync('history', history.slice(0, 20));

    // 同步到后端
    const userId = this.getUserId();
    wx.request({
      url: 'https://sakuranightingale.top/api/mini/update-status',
      method: 'POST',
      data: {
        user_id: userId,
        task_id: card.task_id || card.id,
        read: 1
      }
    });
  },

  // 添加收藏
  addToFavorite(card) {
    const userId = this.getUserId();
    wx.request({
      url: 'https://sakuranightingale.top/api/mini/update-status',
      method: 'POST',
      data: {
        user_id: userId,
        task_id: card.task_id || card.id,
        favorite: 1
      },
      success: () => {
        wx.showToast({ title: '已收藏', icon: 'success' });
      }
    });
  },

  // 重置位置
  resetPosition() {
    this.setData({
      offsetX: 0,
      offsetY: 0,
      showLeftHint: false,
      showRightHint: false
    });
  },

  // 跳转到历史记录
  goToHistory() {
    wx.navigateTo({
      url: '/pages/history/history'
    });
  },

  // 跳转到收藏夹
  goToFavorites() {
    wx.navigateTo({
      url: '/pages/favorites/favorites'
    });
  },

  // 加载卡片数据
  loadCards() {
    const userId = this.getUserId();
    console.log('loadCards - userId:', userId);
    
    if (!userId) {
      console.log('loadCards - 没有 userId');
      return;
    }
    
    wx.request({
      url: `https://sakuranightingale.top/api/mini/results?user_id=${userId}&status=unread`,
      success: (res) => {
        console.log('loadCards - 响应:', res.data);
        if (res.data.code === 200) {
          const results = res.data.results || [];
          console.log('loadCards - results:', results);
          this.setData({
            cards: results,
            noMore: results.length === 0,
            cardAnimation: []
          });
        }
      },
      fail: (err) => {
        console.error('加载卡片失败:', err);
      }
    });
  }
});
