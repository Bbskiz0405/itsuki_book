# Firebase 部署與配置指南

## 📋 已完成的 Firebase 優化

### 1. Security Rules ✅
已建立安全規則檔案，保護你的資料：

#### Firestore Rules (`firestore.rules`)
- ✅ 所有人可讀取圖片
- ✅ 只有認證用戶可以上傳/修改/刪除
- ✅ 預設拒絕其他存取

#### Storage Rules (`storage.rules`)
- ✅ 所有人可讀取圖片
- ✅ 只有認證用戶可以上傳
- ✅ 限制檔案大小 10MB
- ✅ 只允許圖片格式

### 2. Firebase Hosting 配置優化 ✅
`firebase.json` 已優化：
- ✅ 忽略不必要的檔案 (bot.py, .md 等)
- ✅ 設定快取策略 (圖片 7天, JS/CSS 1天)
- ✅ SPA 路由重寫
- ✅ 整合 Firestore 和 Storage Rules

### 3. 前端程式碼重構 ✅
- ✅ 統一使用 `firebase-config.js`
- ✅ 移除重複的 Firebase 初始化程式碼
- ✅ 使用共用函數 `common.js`

## 🚀 部署步驟

### 第一次部署

1. **安裝 Firebase CLI**
```bash
npm install -g firebase-tools
```

2. **登入 Firebase**
```bash
firebase login
```

3. **部署 Security Rules**
```bash
# 部署 Firestore Rules
firebase deploy --only firestore:rules

# 部署 Storage Rules
firebase deploy --only storage:rules
```

4. **部署網站**
```bash
firebase deploy --only hosting
```

### 日常更新部署

```bash
# 只部署網站 (最常用)
firebase deploy --only hosting

# 部署所有內容 (網站 + Rules)
firebase deploy
```

## 🔒 Security Rules 測試

### 測試 Firestore Rules
1. 前往 [Firebase Console](https://console.firebase.google.com/)
2. 選擇你的專案 `itsukibook-1001`
3. 進入 `Firestore Database` > `規則` 標籤
4. 點擊 "規則模擬器" 進行測試

### 測試案例

**✅ 應該允許:**
- 未登入用戶讀取 images collection
- 已登入用戶上傳/修改/刪除圖片

**❌ 應該拒絕:**
- 未登入用戶上傳/修改/刪除圖片
- 上傳超過 10MB 的檔案
- 上傳非圖片格式的檔案

## 📊 效能優化建議

### 已實作 ✅
- 圖片快取策略 (7天)
- JS/CSS 快取策略 (1天)
- 圖片 lazy loading

### 建議進一步優化
1. **圖片壓縮**
   - 使用 Cloud Functions 自動壓縮上傳的圖片
   - 產生不同尺寸的縮圖

2. **CDN 加速**
   - Firebase Hosting 已內建 CDN
   - 確保圖片也透過 CDN 傳送

3. **Service Worker**
   - 實作離線快取
   - 改善重複訪問的載入速度

## 🔧 維護指令

### 查看部署狀態
```bash
firebase hosting:channel:list
```

### 回滾到前一版本
```bash
firebase hosting:clone SOURCE_SITE_ID:SOURCE_CHANNEL_ID TARGET_SITE_ID:live
```

### 查看日誌
```bash
firebase functions:log
```

## ⚠️ 注意事項

### 1. API Key 安全性
- ✅ Firebase API Key 在前端是公開的，這是正常的
- ✅ 安全性透過 Security Rules 控制
- 建議啟用 [Firebase App Check](https://firebase.google.com/docs/app-check) 防止濫用

### 2. 成本控制
監控使用量以避免超出免費額度：
- Firestore: 每日 50,000 次讀取
- Storage: 1GB 儲存空間, 每月 10GB 下載
- Hosting: 每月 10GB 傳輸

### 3. 備份策略
定期備份 Firestore 資料：
```bash
# 手動匯出 (需要設定)
gcloud firestore export gs://[BUCKET_NAME]
```

## 🐛 疑難排解

### 問題 1: Rules 部署失敗
```bash
# 檢查 Rules 語法
firebase deploy --only firestore:rules --debug
```

### 問題 2: 網站未更新
1. 清除瀏覽器快取
2. 使用無痕模式測試
3. 檢查 Firebase Console 的部署記錄

### 問題 3: 圖片上傳失敗
1. 檢查 Storage Rules 是否已部署
2. 確認用戶已登入
3. 檢查檔案大小是否超過 10MB

## 📞 有用的連結

- [Firebase Console](https://console.firebase.google.com/project/itsukibook-1001)
- [Firebase 文件](https://firebase.google.com/docs)
- [Security Rules 參考](https://firebase.google.com/docs/rules)
- [Hosting 配置](https://firebase.google.com/docs/hosting/full-config)

## 📈 監控與分析

### 啟用 Google Analytics
在 `firebase-config.js` 中已經有 `appId`，可以在 Firebase Console 啟用 Analytics：

1. 前往 Firebase Console
2. 選擇 "Analytics"
3. 點擊 "啟用 Google Analytics"

### 監控項目
- 頁面瀏覽量
- 用戶行為
- 圖片抽取次數
- 錯誤率

## ✅ 檢查清單

部署前確認：
- [ ] `firestore.rules` 檔案存在
- [ ] `storage.rules` 檔案存在
- [ ] `firebase.json` 已更新
- [ ] 所有 HTML 都使用 `firebase-config.js`
- [ ] 測試登入功能正常
- [ ] 測試圖片上傳功能正常
- [ ] 測試圖片顯示功能正常

部署後確認：
- [ ] 網站可以正常訪問
- [ ] 圖片可以正常顯示
- [ ] Admin 登入功能正常
- [ ] 圖片上傳功能正常
- [ ] Console 沒有錯誤訊息
