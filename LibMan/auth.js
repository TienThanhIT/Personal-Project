/* auth.js */
 function logout() {
            Swal.fire({
                title: 'Xác nhận đăng xuất?',
                text: "Bạn sẽ bị đẩy ra khỏi hệ thống!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Đăng xuất ngay',
                cancelButtonText: 'Hủy'
            }).then((result) => {
                if (result.isConfirmed) {
                    // 1. Xóa sạch dấu vết đăng nhập
                    localStorage.clear();
                    sessionStorage.clear();
                    
                    // 2. Chuyển hướng bằng replace để xóa lịch sử duyệt web
                    window.location.replace('login.html');
                }
            });
        }

(function() {
    const isLoggedIn = localStorage.getItem('isLoggedIn'); // Hoặc token của bạn
    if (!isLoggedIn && !window.location.href.includes('login.html')) {
        window.location.replace('login.html');
    }
})();

// Kiểm tra định kỳ (Phòng trường hợp người dùng mở nhiều tab và đăng xuất ở tab khác)
setInterval(() => {
    if (!window.location.pathname.includes('login.html')) {
        if (localStorage.getItem('isLoggedIn') !== 'true') {
            window.location.replace('login.html');
        }
    }
}, 2000);