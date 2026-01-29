create database BookLib
use BookLib
create table book(
    book_id varchar(255) primary key,
    tieude varchar(255),
    theloai varchar(255),
    tacgia varchar(255),
    soluong int,
    nxb varchar(255),
    ngaymuon date,
    ngaytra date,
    hantra date,
    trangthai boolean default TRUE
)