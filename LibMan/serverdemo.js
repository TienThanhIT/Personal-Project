const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path');

const app = express(); // Khai báo app ngay từ đầu

app.use(express.json());
app.use(express.static(path.join(__dirname, 'demo')));

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

        // 1. Lấy mã sách từ phiếu mượn để hoàn kho
        const [phieu] = await connection.execute('SELECT book_id FROM phieu_muon WHERE phieu_id = ?', [phieu_id]);
        if (phieu.length === 0) return res.status(404).json({ error: "Không tìm thấy phiếu!" });

        const bookId = phieu[0].book_id;

        // 2. CẬP NHẬT QUAN TRỌNG: Ghi nhận ngày trả VÀ đổi trạng thái thành "Đã trả"
        const sqlUpdatePhieu = `
            UPDATE phieu_muon 
            SET ngay_tra_thuc_te = CURDATE(), 
                trang_thai = 'Đã trả' 
            WHERE phieu_id = ?`;
        await connection.execute(sqlUpdatePhieu, [phieu_id]);

        // 3. Tăng số lượng sách trong kho (conlai)
        await connection.execute('UPDATE sach SET conlai = conlai + 1 WHERE book_id = ?', [bookId]);

        await connection.commit();
        res.json({ message: "Trả sách thành công và đã cập nhật trạng thái!" });
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
        
        // Truy vấn lấy thông tin người mượn (hoten) từ bảng docgia và thông tin sách
        const sql = `
            SELECT 
                pm.phieu_id, 
                dg.hoten, 
                pm.book_id, 
                s.tieude, 
                pm.ngay_muon, 
                pm.han_tra, 
                pm.ngay_tra_thuc_te 
            FROM phieu_muon pm
            JOIN docgia dg ON pm.docgia_id = dg.docgia_id
            JOIN sach s ON pm.book_id = s.book_id
            WHERE pm.ngay_tra_thuc_te IS NOT NULL
            ORDER BY pm.ngay_tra_thuc_te DESC
        `;
        
        const [rows] = await connection.execute(sql);
        res.json(rows);
    } catch (error) {
        console.error("Lỗi API Lịch sử:", error);
        res.status(500).json({ error: "Lỗi hệ thống: " + error.message });
    } finally {
        if (connection) await connection.end();
    }
});
// API lấy danh sách toàn bộ sách trong kho (Đã sửa lỗi db is not defined)
app.get('/api/kho-sach', async (req, res) => {
    let connection;
    try {
        // Khởi tạo kết nối giống các API trên
        connection = await mysql.createConnection(dbConfig);
        
        // Thực hiện câu lệnh SQL lấy toàn bộ sách
        const sql = "SELECT * FROM sach ORDER BY book_id DESC"; 
        const [rows] = await connection.execute(sql);
        
        res.json(rows); // Trả về mảng dữ liệu cho Frontend
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Lỗi hệ thống: " + error.message });
    } finally {
        // Luôn đóng kết nối để tránh quá tải RAM
        if (connection) await connection.end();
    }
});

// 1. API Xóa sách (Kiểm tra xem có ai đang mượn không trước khi xóa)
app.delete('/api/xoa-sach/:id', async (req, res) => {
    const book_id = req.params.id;
    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        
        // 1. Kiểm tra xem sách có trong phiếu mượn không
        const [rows] = await connection.execute(
            'SELECT phieu_id FROM phieu_muon WHERE book_id = ? LIMIT 1', 
            [book_id]
        );

        if (rows.length > 0) {
            return res.status(400).json({ 
                error: "Không thể xóa sách này vì vẫn còn người đang mượn!" 
            });
        }

        // 2. Nếu không có ràng buộc, tiến hành xóa
        await connection.execute('DELETE FROM sach WHERE book_id = ?', [book_id]);
        res.json({ message: "Xóa sách thành công!" });

    } catch (error) {
        res.status(500).json({ error: "Lỗi hệ thống: " + error.message });
    } finally {
        if (connection) await connection.end();
    }
});
// API Sửa sách
app.put('/api/sua-sach/:id', async (req, res) => {
    const { id } = req.params;
    const { tieude, theloai, tacgia } = req.body;
    
    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        
        // Tên bảng của bạn là 'sach' (không phải 'books')
        const sql = "UPDATE sach SET tieude = ?, theloai = ?, tacgia = ? WHERE book_id = ?";
        
        const [result] = await connection.execute(sql, [tieude, theloai, tacgia, id]);
        
        if (result.affectedRows > 0) {
            res.json({ message: "Cập nhật thành công" });
        } else {
            res.status(404).json({ error: "Không tìm thấy mã sách này" });
        }
    } catch (error) {
        console.error("Lỗi cập nhật:", error);
        res.status(500).json({ error: "Lỗi hệ thống: " + error.message });
    } finally {
        if (connection) await connection.end();
    }
});

// API Đăng nhập
app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;
    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        const sql = "SELECT * FROM ngdung WHERE USERNAME = ? AND PASS = ?";
        const [rows] = await connection.execute(sql, [username, password]);

        if (rows.length > 0) {
            res.json({ success: true, message: "Đăng nhập thành công!" });
        } else {
            res.status(401).json({ success: false, message: "Sai tài khoản hoặc mật khẩu!" });
        }
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    } finally {
        if (connection) await connection.end();
    }
});


app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'demo'));
});

app.use('/img', express.static(path.join(__dirname, 'img')));

app.listen(3000, () => {
    console.log(' Server đang chạy tại http://localhost:3000');
});