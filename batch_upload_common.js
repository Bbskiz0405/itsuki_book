// 批量上傳專用的共用函數
// 引入 common.js 中的 addLog 函數

// 全域變量
let csvData = [];
let imageFiles = {};
let uploadQueue = [];
let currentBatch = 0;
let totalBatches = 0;
let isPaused = false;
let isStopped = false;
let stats = {
    total: 0,
    success: 0,
    error: 0,
    skipped: 0
};

// CSV 解析
function parseCSV(csv) {
    const lines = csv.split('\n');
    const data = [];

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        const cols = line.split(',');
        if (cols.length >= 2 && cols[0] && cols[1]) {
            data.push({
                id: parseInt(cols[0]),
                text: cols[1].trim(),
                format: cols[2] ? cols[2].trim() : 'jpg'
            });
        }
    }

    return data;
}

// 準備上傳佇列
function prepareUploadQueue(startNum, endNum, batchSize) {
    uploadQueue = [];
    const start = parseInt(startNum);
    const end = parseInt(endNum);
    const batch = parseInt(batchSize);

    for (let i = start; i <= end; i++) {
        const csvItem = csvData.find(item => item.id === i);
        const imageFile = imageFiles[i];

        if (csvItem && imageFile) {
            uploadQueue.push({
                id: i,
                text: csvItem.text,
                file: imageFile,
                filename: `${i}.jpg`
            });
        } else {
            addLog(`跳過編號 ${i}：${!csvItem ? '缺少語錄' : '缺少圖片'}`, 'info');
            stats.skipped++;
        }
    }

    totalBatches = Math.ceil(uploadQueue.length / batch);
    return uploadQueue.length;
}

// 上傳單個項目
async function uploadSingleItem(item) {
    try {
        // 檢查是否已存在
        const existingQuery = await db.collection('images')
            .where('text', '==', item.text)
            .where('name', '==', item.filename)
            .get();

        if (!existingQuery.empty) {
            addLog(`跳過 ${item.filename}：已存在相同項目`, 'info');
            stats.skipped++;
            updateStats();
            return;
        }

        // 上傳到 Storage
        const storageRef = storage.ref(`images/${Date.now()}_${item.filename}`);
        const snapshot = await storageRef.put(item.file);
        const downloadURL = await snapshot.ref.getDownloadURL();

        // 儲存到 Firestore
        await db.collection('images').add({
            name: item.filename,
            text: item.text,
            imageUrl: downloadURL,
            originalId: item.id,
            createdAt: firebase.firestore.FieldValue.serverTimestamp()
        });

        addLog(`✅ ${item.filename}: ${item.text.substring(0, 20)}...`, 'success');
        stats.success++;

    } catch (error) {
        addLog(`❌ ${item.filename}: ${error.message}`, 'error');
        stats.error++;
        console.error('Upload error:', error);
    }

    updateStats();
}

// 更新統計
function updateStats() {
    document.getElementById('totalCount').textContent = stats.total;
    document.getElementById('successCount').textContent = stats.success;
    document.getElementById('errorCount').textContent = stats.error;
    document.getElementById('skippedCount').textContent = stats.skipped;
}

// 更新進度
function updateProgress(batchSize) {
    const totalProcessed = currentBatch * parseInt(batchSize);
    const progress = Math.min((totalProcessed / uploadQueue.length) * 100, 100);
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    progressBar.style.width = progress + '%';
    progressBar.textContent = Math.round(progress) + '%';
    progressText.textContent = `已處理 ${Math.min(totalProcessed, uploadQueue.length)} / ${uploadQueue.length} 項目`;
}
