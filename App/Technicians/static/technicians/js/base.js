// Sidebar toggle logic
const toggleBtn = document.getElementById("toggleSidebar");
const sidebar = document.getElementById("sidebar");
const content = document.getElementById("content");

toggleBtn.addEventListener("click", () => {
  if (window.innerWidth > 992) {
    sidebar.classList.toggle("collapsed");
    content.classList.toggle("expanded");
  } else {
    sidebar.classList.toggle("active");
  }
});
