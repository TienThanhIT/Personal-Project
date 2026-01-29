// API Tìm kiếm độc giả theo tên để gợi ý
const express = require('express'); // 1. Khai báo thư viện
const mysql = require('mysql2/promise');
const path = require('path');

const app = express(); // 2. KHỞI TẠO BIẾN APP (Dòng này bạn đang thiếu!)

app.use(express.json());
app.use(express.static('public')); 

// Cấu hình kết nối
const dbConfig = {
    host: '127.0.0.1',
    user: 'root',
    password: '', // Để trống nếu dùng XAMPP mặc định
    database: 'BookLib'
};

// Route mặc định
app.get('/', (req, res) => {
    res.send('Server đã chạy thành công! Hãy truy cập /muon-sach.html');
});

app.get('/api/tim-doc-gia', async (req, res) => {
    const name = req.query.name;
    try {
        const connection = await mysql.createConnection(dbConfig);
        // Tìm kiếm gần đúng (LIKE)
        const [rows] = await connection.execute(
            'SELECT docgia_id, hoten FROM docgia WHERE hoten LIKE ? LIMIT 5',
            [`%${name}%`]
        );
        await connection.end();
        res.json(rows);
    } catch (error) {
        res.status(500).json({ error: "Lỗi tìm kiếm" });
    }
});

app.listen(3000, () => console.log('🚀 Server đang chạy tại http://localhost:3000'));