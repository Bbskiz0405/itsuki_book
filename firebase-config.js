// Firebase 配置文件
// 建議: 請將 API Key 等敏感資訊改用環境變數或 Firebase Hosting 的環境配置
const firebaseConfig = {
    apiKey: "AIzaSyC8nvSRxtfpXxQvlRqzIzXQvcOZZ_UhDk8",
    authDomain: "itsukibook-1001.firebaseapp.com",
    projectId: "itsukibook-1001",
    storageBucket: "itsukibook-1001.firebasestorage.app",
    messagingSenderId: "173649948415",
    appId: "1:173649948415:web:4f8117a112232a7f75e6ca"
};

// 初始化 Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();
const auth = firebase.auth();
const storage = firebase.storage();
