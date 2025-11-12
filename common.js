// 共用 JavaScript 函數

/**
 * 切換側邊選單的顯示/隱藏
 */
function toggleMenu() {
    const menu = document.getElementById('menu');
    const overlay = document.getElementById('overlay');
    const menuButton = document.getElementById('menuButton');

    if (menu.style.right === '0px') {
        menu.style.right = '-350px';
        overlay.style.display = 'none';
        menuButton.style.display = 'flex';
        setTimeout(() => {
            menuButton.style.justifyContent = 'space-evenly';
        }, 300);
    } else {
        menu.style.right = '0px';
        overlay.style.display = 'block';
        menuButton.style.display = 'none';
    }
}

/**
 * 從 Firestore 獲取隨機圖片
 * @returns {Promise<Object|null>} 隨機圖片物件或 null
 */
async function getRandomImageFromFirestore() {
    try {
        const snapshot = await db.collection('images').get();
        const images = [];

        snapshot.forEach(doc => {
            const data = doc.data();
            if (data.imageUrl) {
                images.push({
                    url: data.imageUrl,
                    name: data.name || '未命名圖片',
                    text: data.text || ''
                });
            }
        });

        if (images.length === 0) {
            console.warn('沒有可用的圖片');
            return null;
        }

        return images[Math.floor(Math.random() * images.length)];
    } catch (error) {
        console.error('獲取圖片時出錯:', error);
        throw error;
    }
}

/**
 * 顯示隨機答案圖片
 */
async function showRandomAnswer() {
    try {
        const randomImage = await getRandomImageFromFirestore();

        if (!randomImage) {
            alert('目前沒有可用的圖片，請稍後再試');
            return;
        }

        // 顯示圖片
        const imgElement = document.getElementById('answerImage');
        if (imgElement) {
            imgElement.src = randomImage.url;
            imgElement.alt = randomImage.name;
            imgElement.style.display = 'block';
        }

        // 更新圖片資訊
        const imgNameElement = document.getElementById('imageName');
        if (imgNameElement) {
            imgNameElement.textContent = randomImage.name;
        }

        const imgTextElement = document.getElementById('imageText');
        if (imgTextElement) {
            imgTextElement.textContent = randomImage.text;
        }

        // 控制按鈕顯示
        const revealButton = document.getElementById('revealButton');
        const nextButton = document.getElementById('nextButton');
        if (revealButton && revealButton.style.display !== 'none') {
            revealButton.style.display = 'none';
            if (nextButton) nextButton.style.display = 'inline-block';
        }

    } catch (error) {
        console.error('獲取圖片時出錯:', error);
        alert('獲取圖片時出錯，請稍後再試');
    }
}

/**
 * 添加日誌條目到日誌容器
 * @param {string} message - 日誌訊息
 * @param {string} type - 日誌類型 (info|success|error)
 */
function addLog(message, type = 'info') {
    const logContent = document.getElementById('logContent');
    if (!logContent) return;

    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContent.appendChild(logEntry);
    logContent.scrollTop = logContent.scrollHeight;
}
