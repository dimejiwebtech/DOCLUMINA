// Mobile services dropdown state
let isMobileDropdownOpen = false;

// Theme toggle functionality
const toggleTheme = () => {
  const html = document.documentElement;
  const themeIcon = document.getElementById('theme-icon');
  const isDark = html.classList.toggle('dark');

  localStorage.setItem('theme', isDark ? 'dark' : 'light');
};

// Mobile menu toggle functionality
const toggleMobileMenu = () => {
  const sidebar = document.getElementById('mobile-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const isCurrentlyOpen = !sidebar.classList.contains('-translate-x-full');

  if (isCurrentlyOpen) {
    sidebar.classList.add('-translate-x-full');
    overlay.classList.add('opacity-0', 'invisible');
    document.body.classList.remove('overflow-hidden');
  } else {
    sidebar.classList.remove('-translate-x-full');
    overlay.classList.remove('opacity-0', 'invisible');
    document.body.classList.add('overflow-hidden');
  }
};

// Mobile services dropdown toggle - pure CSS approach
const toggleMobileServicesDropdown = () => {
  const dropdown = document.getElementById('mobile-services-dropdown');
  const arrow = document.getElementById('mobile-services-arrow');

  if (isMobileDropdownOpen) {
    dropdown.classList.remove('max-h-96');
    dropdown.classList.add('max-h-0');
    arrow.classList.remove('rotate-180');
    isMobileDropdownOpen = false;
  } else {
    dropdown.classList.remove('max-h-0');
    dropdown.classList.add('max-h-96');
    arrow.classList.add('rotate-180');
    isMobileDropdownOpen = true;
  }
};

// Desktop services dropdown hover functionality
const showDesktopServicesDropdown = () => {
  const dropdown = document.getElementById('desktop-services-dropdown');
  const arrow = document.getElementById('desktop-services-arrow');

  dropdown.classList.remove('opacity-0', 'invisible', 'translate-y-2');
  dropdown.classList.add('opacity-100', 'visible', 'translate-y-0');
  arrow.classList.add('rotate-180');
};

const hideDesktopServicesDropdown = () => {
  const dropdown = document.getElementById('desktop-services-dropdown');
  const arrow = document.getElementById('desktop-services-arrow');

  dropdown.classList.add('opacity-0', 'invisible', 'translate-y-2');
  dropdown.classList.remove('opacity-100', 'visible', 'translate-y-0');
  arrow.classList.remove('rotate-180');
};

// Close mobile menu when clicking outside
const closeMobileMenuOnOutsideClick = (e) => {
  const sidebar = document.getElementById('mobile-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const mobileMenuButton = document.getElementById('mobile-menu');
  const isOpen = !sidebar.classList.contains('-translate-x-full');

  if (
    isOpen &&
    !sidebar.contains(e.target) &&
    !mobileMenuButton.contains(e.target)
  ) {
    toggleMobileMenu();
  }
};

// Initialize theme and event listeners on page load
document.addEventListener('DOMContentLoaded', () => {
  // Set initial theme based on saved preference or system preference


  // Event listeners
  document
    .getElementById('theme-toggle')
    .addEventListener('click', toggleTheme);
  document
    .getElementById('mobile-menu')
    .addEventListener('click', toggleMobileMenu);
  document
    .getElementById('close-sidebar')
    .addEventListener('click', toggleMobileMenu);
  document
    .getElementById('sidebar-overlay')
    .addEventListener('click', toggleMobileMenu);
  document
    .getElementById('mobile-services-toggle')
    .addEventListener('click', toggleMobileServicesDropdown);

  // Desktop dropdown hover events
  const desktopServicesContainer = document.getElementById(
    'desktop-services-container'
  );
  desktopServicesContainer.addEventListener(
    'mouseenter',
    showDesktopServicesDropdown
  );
  desktopServicesContainer.addEventListener(
    'mouseleave',
    hideDesktopServicesDropdown
  );

  // Close sidebar when clicking outside
  document.addEventListener('click', closeMobileMenuOnOutsideClick);
});



// Dropdown functionality
const moreBtn = document.getElementById('moreBtn');
const moreDropdown = document.getElementById('moreDropdown');
const moreIcon = document.getElementById('moreIcon');

moreBtn.addEventListener('click', () => {
  const isVisible = !moreDropdown.classList.contains('opacity-0');

  if (isVisible) {
    moreDropdown.classList.add('opacity-0', 'invisible');
    moreIcon.style.transform = 'rotate(0deg)';
  } else {
    moreDropdown.classList.remove('opacity-0', 'invisible');
    moreIcon.style.transform = 'rotate(180deg)';
  }
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
  if (!moreBtn.contains(e.target) && !moreDropdown.contains(e.target)) {
    moreDropdown.classList.add('opacity-0', 'invisible');
    moreIcon.style.transform = 'rotate(0deg)';
  }
});


// Social Share Buttons

function shareOnFacebook() {
  const url = encodeURIComponent(window.location.href);
  window.open(
    `https://www.facebook.com/sharer/sharer.php?u=${url}`,
    '_blank',
    'width=600,height=400'
  );
}

function shareOnWhatsApp() {
  const url = encodeURIComponent(window.location.href);
  const text = encodeURIComponent(document.title);
  window.open(`https://wa.me/?text=${text} ${url}`, '_blank');
}

function shareOnTwitter() {
  const url = encodeURIComponent(window.location.href);
  const text = encodeURIComponent(document.title);
  window.open(
    `https://twitter.com/intent/tweet?text=${text}&url=${url}`,
    '_blank',
    'width=600,height=400'
  );
}

function shareOnLinkedIn() {
  const url = encodeURIComponent(window.location.href);
  window.open(
    `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
    '_blank',
    'width=600,height=400'
  );
}

function shareOnThreads() {
  const url = encodeURIComponent(window.location.href);
  const text = encodeURIComponent(document.title);
  window.open(
    `https://threads.net/intent/post?text=${text} ${url}`,
    '_blank',
    'width=600,height=400'
  );
}


  // Counter animation for stats
        function animateCounters() {
            const counters = document.querySelectorAll('.counter');
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const target = parseInt(entry.target.dataset.target);
                        const duration = 2000;
                        const increment = target / (duration / 16);
                        let current = 0;
                        
                        const timer = setInterval(() => {
                            current += increment;
                            if (current >= target) {
                                current = target;
                                clearInterval(timer);
                            }
                            
                            if (target >= 1000) {
                                entry.target.textContent = Math.floor(current).toLocaleString() + '+';
                            } else {
                                entry.target.textContent = Math.floor(current) + '+';
                            }
                        }, 16);
                        
                        observer.unobserve(entry.target);
                    }
                });
            });
            
            counters.forEach(counter => observer.observe(counter));
        }
        
        // Initialize animations when DOM is loaded
        document.addEventListener('DOMContentLoaded', animateCounters);

document.addEventListener('DOMContentLoaded', function () {
  const backToTopBtn = document.getElementById('backToTop');

  function toggleBackToTopButton() {
    const scrolled = window.scrollY;
    const documentHeight = document.documentElement.scrollHeight;
    const windowHeight = window.innerHeight;

    // Show when user has scrolled 80% of the page or within 800px of bottom
    const threshold = Math.min(
      documentHeight * 0.8,
      documentHeight - windowHeight - 800
    );

    if (scrolled >= threshold) {
      backToTopBtn.classList.remove('opacity-0', 'invisible');
      backToTopBtn.classList.add('opacity-100', 'visible');
    } else {
      backToTopBtn.classList.add('opacity-0', 'invisible');
      backToTopBtn.classList.remove('opacity-100', 'visible');
    }
  }

  // Smooth scroll to top
  backToTopBtn.addEventListener('click', function () {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  });

  // Check on scroll
  window.addEventListener('scroll', toggleBackToTopButton);

  // Initial check
  toggleBackToTopButton();
});