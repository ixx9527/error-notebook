Component({
  data: {
    selected: 0,
    theme: 'light',
    list: [
      {
        pagePath: "/pages/index/index",
        iconPath: "/assets/icons-svg/home_muted.svg",
        selectedIconPath: "/assets/icons-svg/home_primary.svg",
        iconDarkPath: "/assets/icons-svg/home_muted_dark.svg",
        selectedIconDarkPath: "/assets/icons-svg/home_primary_dark.svg"
      },
      {
        pagePath: "/pages/error-list/error-list",
        iconPath: "/assets/icons-svg/book_muted.svg",
        selectedIconPath: "/assets/icons-svg/book_primary.svg",
        iconDarkPath: "/assets/icons-svg/book_muted_dark.svg",
        selectedIconDarkPath: "/assets/icons-svg/book_primary_dark.svg"
      },
      {
        pagePath: "/pages/profile/profile",
        iconPath: "/assets/icons-svg/user_muted.svg",
        selectedIconPath: "/assets/icons-svg/user_primary.svg",
        iconDarkPath: "/assets/icons-svg/user_muted_dark.svg",
        selectedIconDarkPath: "/assets/icons-svg/user_primary_dark.svg"
      }
    ]
  },
  lifetimes: {
    attached() {
      // 获取系统主题
      const systemInfo = wx.getWindowInfo();
      const theme = systemInfo.theme || 'light';
      
      // 获取当前页面路径，设置选中状态
      const pages = getCurrentPages();
      const currentPage = pages[pages.length - 1];
      const currentPath = currentPage ? '/' + currentPage.route : '';

      const index = this.data.list.findIndex(item => item.pagePath === currentPath);

      this.setData({
        selected: index !== -1 ? index : 0,
        theme: theme
      });
    }
  },
  methods: {
    switchTab(e) {
      const data = e.currentTarget.dataset;
      const url = data.path;
      wx.switchTab({ url });
    }
  }
});
