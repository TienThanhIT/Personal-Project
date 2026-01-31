CREATE DATABASE BookLib;
USE BookLib;

-- 1. Bảng lưu trữ thông tin sách
CREATE TABLE sach (
    book_id VARCHAR(50) PRIMARY KEY,
    tieude VARCHAR(255) NOT NULL,
    theloai VARCHAR(100),
    tacgia VARCHAR(255),
    nxb VARCHAR(255),
    namxb YEAR,
    tongso INT DEFAULT 0,
    conlai INT DEFAULT 0
);

-- 2. Bảng lưu trữ thông tin độc giả
CREATE TABLE docgia (
    docgia_id INT PRIMARY KEY AUTO_INCREMENT, 
    hoten VARCHAR(255) NOT NULL,
    donvi VARCHAR(255),
    sdt VARCHAR(15)
);

-- 3. Bảng quản lý mượn trả
CREATE TABLE phieu_muon (
    phieu_id INT PRIMARY KEY AUTO_INCREMENT,
    book_id VARCHAR(50),
    docgia_id INT,
    ngay_muon DATE,
    han_tra DATE,
    ngay_tra_thuc_te DATE DEFAULT NULL,
    trang_thai VARCHAR(50) DEFAULT 'Đang mượn',
    FOREIGN KEY (book_id) REFERENCES sach(book_id),
    FOREIGN KEY (docgia_id) REFERENCES docgia(docgia_id)
);