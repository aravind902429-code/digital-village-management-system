// Custom JavaScript for Digital Village
document.addEventListener('DOMContentLoaded', function() {
    console.log("Digital Village App Loaded");
    
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
});
