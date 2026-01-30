const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const dbConfig = {
    host: '127.0.0.1',
    user: 'root',
    password: '', 
    database: 'BookLib'
};

// Route mặc định
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'muon.html'));
});

// API Tìm kiếm độc giả (Để hiện gợi ý khi gõ tên)
app.get('/api/tim-doc-gia', async (req, res) => {
    const name = req.query.name;
    try {
        const connection = await mysql.createConnection(dbConfig);
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

// API Thực hiện mượn sách
app.post('/api/muon-sach', async (req, res) => {
    const { book_id, docgia_id, ngay_muon, han_tra } = req.body;
    
    // Kiểm tra ngày phía Server (Bảo mật)
    if (new Date(han_tra) <= new Date(ngay_muon)) {
        return res.status(400).json({ error: "Ngày trả phải sau ngày mượn!" });
    }

    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        await connection.beginTransaction();

        // 1. Kiểm tra sách còn không (Lưu ý: dùng tên cột 'conlai' theo SQL của bạn)
        const [books] = await connection.execute(
            'SELECT conlai FROM sach WHERE book_id = ? FOR UPDATE', [book_id]
        );

        if (books.length === 0) throw new Error('Mã sách không tồn tại!');
        if (books[0].conlai <= 0) throw new Error('Sách này đã hết trong kho!');

        // 2. Tạo phiếu mượn
        await connection.execute(
            'INSERT INTO phieu_muon (book_id, docgia_id, ngay_muon, han_tra, trang_thai) VALUES (?, ?, ?, ?, "Dang muon")',
            [book_id, docgia_id, ngay_muon, han_tra]
        );

        // 3. Trừ số lượng sách (UPDATE cột 'conlai')
        await connection.execute(
            'UPDATE sach SET conlai = conlai - 1 WHERE book_id = ?', [book_id]
        );

        await connection.commit();
        res.json({ message: "Cho mượn sách thành công!" });

    } catch (error) {
        if (connection) await connection.rollback();
        res.status(400).json({ error: error.message });
    } finally {
        if (connection) await connection.end();
    }
});

app.listen(3000, () => {
    console.log('Server đang chạy tại http://localhost:3000');
});