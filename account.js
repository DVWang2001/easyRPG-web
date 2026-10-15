// 共用地基：初始化 Firebase、Google 登入、Firestore handle。
// 之後留言/評分/收藏…等功能都 import 這支。
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js';
import {
  getAuth, GoogleAuthProvider, signInWithPopup,
  signOut as fbSignOut, onAuthStateChanged,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-auth.js';
import { getFirestore } from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import { firebaseConfig, ADMIN_UID } from './firebase-config.js';

let app, auth, db, ok = false;
try {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  db = getFirestore(app);
  ok = true;
} catch (e) {
  console.error('Firebase 初始化失敗', e);
}

export { db, auth, ADMIN_UID };

// 設定檔還是佔位符（YOUR_*）時視為「未設定」，讓 UI 給友善提示而非報錯。
export function isReady() {
  return ok && !String(firebaseConfig.apiKey || '').startsWith('YOUR_');
}
export function currentUser() { return auth ? auth.currentUser : null; }
export function onAuthChange(cb) { if (auth) onAuthStateChanged(auth, cb); }
export function signInWithGoogle() {
  if (!auth) return Promise.reject(new Error('Firebase 未初始化'));
  return signInWithPopup(auth, new GoogleAuthProvider());
}
export function signOutUser() {
  if (!auth) return Promise.reject(new Error('Firebase 未初始化'));
  return fbSignOut(auth);
}
export function isAdmin(uid) { return !!uid && uid === ADMIN_UID; }
