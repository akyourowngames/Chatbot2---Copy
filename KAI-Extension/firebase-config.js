// KAI Extension - Firebase Config
// This config MUST match Frontend/services/FirebaseService.ts

const firebaseConfig = {
    apiKey: "AIzaSyAVv4EhUiVZSf54iZlB-ud05pxIlO8zBWk",
    authDomain: "kai-g-80f9c.firebaseapp.com",
    projectId: "kai-g-80f9c",
    storageBucket: "kai-g-80f9c.appspot.com",
    messagingSenderId: "125633190886",
    appId: "1:125633190886:web:65e1a7b4f59048a1768853",
    measurementId: "G-PJBCQQRWCQ"
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = firebaseConfig;
}
