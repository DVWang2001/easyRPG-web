// 範本：複製成同目錄的 `firebase-config.js` 後填入你自己的值。
// firebase-config.js 已被 .gitignore，金鑰不會進版控。
// （Firebase web config 與圖床 key 一定會出現在部署後的前端 JS——這對瀏覽器端上傳是無法避免的；
//   安全靠 Firestore 規則，不靠藏這些值。把它們留在 git 外只是避免被 GitHub 爬蟲掃到。）
//
// 取得方式：
//   firebaseConfig → Firebase Console → 專案設定 → 您的應用程式 → 網頁應用程式
//   ADMIN_UID      → 自己登入網站一次後，Firebase Console → Authentication → Users 複製你的 uid
//   imageUpload    → imgbb：登入 https://api.imgbb.com 自助取得 API key（免費）
export const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT",
  storageBucket: "YOUR_PROJECT.firebasestorage.app",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
};

export const ADMIN_UID = "YOUR_ADMIN_UID";

export const imageUpload = { provider: "imgbb", apiKey: "YOUR_IMGBB_API_KEY" };
