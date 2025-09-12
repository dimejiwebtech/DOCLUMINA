// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
  // Mobile menu toggle
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  if (mobileToggle && sidebar && overlay) {
    mobileToggle.addEventListener('click', function () {
      sidebar.classList.toggle('-translate-x-full');
      overlay.classList.toggle('hidden');
    });

    // Close sidebar when clicking overlay
    overlay.addEventListener('click', function () {
      sidebar.classList.add('-translate-x-full');
      overlay.classList.add('hidden');
    });
  }

  // Toggle submenu function
  window.toggleSubmenu = function (event, submenuId) {
    event.preventDefault();

    if (window.innerWidth < 1024) {
      const submenu = document.getElementById(submenuId);
      if (submenu) {
        submenu.classList.toggle('open');
      }
    }
  };

  // Toggle sidebar collapse/expand
  window.toggleSidebar = function (event) {
    if (event) event.preventDefault();

    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const collapseIcon = document.getElementById('collapse-icon');

    if (window.innerWidth >= 1024 && sidebar && mainContent && collapseIcon) {
      sidebar.classList.toggle('sidebar-collapsed');

      if (sidebar.classList.contains('sidebar-collapsed')) {
        mainContent.classList.remove('lg:ml-64');
        mainContent.classList.add('main-content-collapsed');
        collapseIcon.classList.remove('fa-angle-double-left');
        collapseIcon.classList.add('fa-angle-double-right');
      } else {
        mainContent.classList.add('lg:ml-64');
        mainContent.classList.remove('main-content-collapsed');
        collapseIcon.classList.remove('fa-angle-double-right');
        collapseIcon.classList.add('fa-angle-double-left');
      }
    }
  };

  // Close all submenus when clicking outside
  document.addEventListener('click', function (event) {
    if (!event.target.closest('.dropdown')) {
      const submenus = document.querySelectorAll('.submenu');
      submenus.forEach((submenu) => submenu.classList.remove('open'));
    }
  });
});
