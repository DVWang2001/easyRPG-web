// 站長填入：Firebase 專案 web config（Firebase Console → 專案設定 → 您的應用程式 → 網頁應用程式）。
// 這些值非機密（安全靠 Firestore 規則）。填好後重新「重建並部署」即生效。
export const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT",
  storageBucket: "YOUR_PROJECT.firebasestorage.app",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
};

// 站長的 Google uid（自己登入後可在 Firebase Console 的 Authentication 使用者列表查到）。
// 前端據此顯示「刪除任意攻略」；真正把關在 Firestore 規則。
export const ADMIN_UID = "YOUR_ADMIN_UID";

// 圖床設定：imgur 匿名上傳需 Client-ID（到 imgur 申請應用程式即得，免費、免綁卡）。
export const imageUpload = { provider: "imgur", clientId: "YOUR_IMGUR_CLIENT_ID" };
