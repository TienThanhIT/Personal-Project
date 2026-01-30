const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path');

const app = express(); // Khai báo app ngay từ đầu

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const dbConfig = {
    host: '127.0.0.1',
    user: 'root',
    password: '', 
    database: 'BookLib'
};

// API Nhập sách mới
app.post('/api/nhap-sach', async (req, res) => {
    // Nhận dữ liệu từ payload gửi lên
    const { book_id, tieude, theloai, tacgia, nxb, namxb, tongso } = req.body;

    // Kiểm tra dữ liệu bắt buộc
    if (!book_id || !tieude || !tongso) {
        return res.status(400).json({ error: "Vui lòng nhập Mã sách, Tiêu đề và Số lượng!" });
    }

    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        
        // 1. Kiểm tra trùng mã sách
        const [rows] = await connection.execute('SELECT book_id FROM sach WHERE book_id = ?', [book_id]);
        if (rows.length > 0) {
            return res.status(400).json({ error: "Mã sách này đã tồn tại trong kho!" });
        }

        // 2. Chèn dữ liệu mới vào bảng sach
        // Thứ tự cột: book_id, tieude, theloai, tacgia, nxb, namxb, tongso, conlai
        const sql = `INSERT INTO sach (book_id, tieude, theloai, tacgia, nxb, namxb, tongso, conlai) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`;
        
        await connection.execute(sql, [
            book_id, 
            tieude, 
            theloai || null, 
            tacgia || null, 
            nxb || null, 
            namxb || null, 
            tongso, 
            tongso // conlai lúc mới nhập bằng đúng số lượng tổng
        ]);

        res.json({ message: "Đã thêm sách vào kho thành công!" });

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Lỗi hệ thống: " + error.message });
    } finally {
        if (connection) await connection.end();
    }
});

// API Thực hiện mượn sách
app.post('/api/muon-sach', async (req, res) => {
    // 1. Nhận đúng biến book_id từ Client gửi lên
    const { hoten, don_vi, sdt, book_id, han_tra } = req.body;

    if (!hoten || !book_id || !han_tra) {
        return res.status(400).json({ error: "Thiếu thông tin bắt buộc!" });
    }

    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        await connection.beginTransaction();

        // BƯỚC 1: Kiểm tra book_id có tồn tại không
        const [books] = await connection.execute(
            'SELECT book_id, conlai FROM sach WHERE book_id = ?', 
            [book_id] // Sử dụng book_id
        );

        if (books.length === 0) {
            await connection.rollback();
            return res.status(404).json({ error: "Mã sách này không tồn tại trong hệ thống!" });
        }

        const sachHienTai = books[0];
        if (sachHienTai.conlai <= 0) {
            await connection.rollback();
            return res.status(400).json({ error: "Sách này đã hết trong kho!" });
        }

        // BƯỚC 2: Lưu độc giả
        const [resultDG] = await connection.execute(
            'INSERT INTO docgia (hoten, donvi, sdt) VALUES (?, ?, ?)',
            [hoten, don_vi || null, sdt || null]
        );
        const docgia_id = resultDG.insertId;

        // BƯỚC 3: Lưu phiếu mượn (Dùng CURDATE() cho ngày mượn)
        await connection.execute(
            'INSERT INTO phieu_muon (book_id, docgia_id, ngay_muon, han_tra) VALUES (?, ?, CURDATE(), ?)',
            [book_id, docgia_id, han_tra] 
        );

        // BƯỚC 4: Trừ số lượng sách
        await connection.execute(
            'UPDATE sach SET conlai = conlai - 1 WHERE book_id = ?',
            [book_id]
        );

        await connection.commit();
        res.json({ message: "Cho mượn thành công!" });

    } catch (error) {
        if (connection) await connection.rollback();
        res.status(500).json({ error: "Lỗi hệ thống: " + error.message });
    } finally {
        if (connection) await connection.end();
    }
});

// API Lấy danh sách người mượn (Kết hợp 3 bảng)
app.get('/api/danh-sach-muon', async (req, res) => {
    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        
        const sql = `
            SELECT 
                pm.phieu_id, 
                dg.hoten, 
                dg.sdt, 
                s.book_id, 
                s.tieude, 
                pm.ngay_muon, 
                pm.han_tra 
            FROM phieu_muon pm
            JOIN docgia dg ON pm.docgia_id = dg.docgia_id
            JOIN sach s ON pm.book_id = s.book_id
            WHERE pm.ngay_tra_thuc_te IS NULL
            ORDER BY pm.ngay_muon DESC
        `;
        
        const [rows] = await connection.execute(sql);
        res.json(rows);
    } catch (error) {
        res.status(500).json({ error: "Lỗi hệ thống: " + error.message });
    } finally {
        if (connection) await connection.end();
    }
});

// API Xử lý trả sách
app.post('/api/tra-sach', async (req, res) => {
    const { phieu_id } = req.body;
    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        await connection.beginTransaction();

        // 1. Lấy mã sách từ phiếu mượn
        const [phieu] = await connection.execute('SELECT book_id FROM phieu_muon WHERE phieu_id = ?', [phieu_id]);
        if (phieu.length === 0) return res.status(404).json({ error: "Không tìm thấy phiếu!" });

        const bookId = phieu[0].book_id;

        // 2. Cập nhật ngày trả thực tế là hôm nay (CURDATE())
        await connection.execute('UPDATE phieu_muon SET ngay_tra_thuc_te = CURDATE() WHERE phieu_id = ?', [phieu_id]);

        // 3. Tăng số lượng sách trong kho
        await connection.execute('UPDATE sach SET conlai = conlai + 1 WHERE book_id = ?', [bookId]);

        await connection.commit();
        res.json({ message: "Trả sách thành công!" });
    } catch (error) {
        if (connection) await connection.rollback();
        res.status(500).json({ error: error.message });
    } finally {
        if (connection) await connection.end();
    }
});

app.get('/api/lich-su-tra', async (req, res) => {
    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        // Chỉ lấy những người đã trả sách (ngay_tra_thuc_te IS NOT NULL)
        const sql = `
            SELECT dg.hoten, s.book_id, s.tieude, pm.ngay_muon, pm.han_tra, pm.ngay_tra_thuc_te 
            FROM phieu_muon pm
            JOIN docgia dg ON pm.docgia_id = dg.docgia_id
            JOIN sach s ON pm.book_id = s.book_id
            WHERE pm.ngay_tra_thuc_te IS NOT NULL
            ORDER BY pm.ngay_tra_thuc_te DESC`;
        const [rows] = await connection.execute(sql);
        res.json(rows);
    } catch (error) {
        res.status(500).json({ error: error.message });
    } finally {
        if (connection) await connection.end();
    }
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'muon.html'));
});

app.listen(3000, () => {
    console.log(' Server đang chạy tại http://localhost:3000');
});