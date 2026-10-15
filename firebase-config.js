// 站長填入：Firebase 專案 web config（Firebase Console → 專案設定 → 您的應用程式 → 網頁應用程式）。
// 這些值非機密（安全靠 Firestore 規則）。填好後重新「重建並部署」即生效。
export const firebaseConfig = {
  apiKey: "AIzaSyAWEQCtLdfHH8zlWMMqfCIUSxx6hhz3EXo",
  authDomain: "easyrpg-web.firebaseapp.com",
  projectId: "easyrpg-web",
  storageBucket: "easyrpg-web.firebasestorage.app",
  messagingSenderId: "919840111568",
  appId: "1:919840111568:web:89bb0272ce6ae304f857d5",
  measurementId: "G-28ZCCND0VE"
};

// 站長的 Google uid（自己登入後可在 Firebase Console 的 Authentication 使用者列表查到）。
// 前端據此顯示「刪除任意攻略」；真正把關在 Firestore 規則。
export const ADMIN_UID = "R55euK52xoYpGd1U2CD7kN1bnmX2";

// 圖床設定：imgbb 上傳需 API key（登入 https://api.imgbb.com 自助點一下即得，免費）。
export const imageUpload = { provider: "imgbb", apiKey: "eddf63c0590de5a0d89da3b980ace22a" };
