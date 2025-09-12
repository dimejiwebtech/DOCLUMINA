// Tab functionality
function showTab(tabName) {
  // Hide all tab contents
  document.querySelectorAll('.tab-content').forEach((content) => {
    content.classList.add('hidden');
  });

  // Remove active class from all tabs
  document.querySelectorAll('.tab-button').forEach((button) => {
    button.classList.remove('active', 'border-blue-500', 'text-blue-600');
    button.classList.add('border-transparent', 'text-gray-500');
  });

  // Show selected tab content
  document.getElementById(tabName + '-content').classList.remove('hidden');

  // Add active class to selected tab
  const activeTab = document.getElementById(tabName + '-tab');
  activeTab.classList.add('active', 'border-blue-500', 'text-blue-600');
  activeTab.classList.remove('border-transparent', 'text-gray-500');
}

// Image preview functionality
const imageInput = document.getElementById(
  '{{ profile_form.profile_image.id_for_label }}'
);
if (imageInput) {
  imageInput.addEventListener('change', function (e) {
    if (e.target.files && e.target.files[0]) {
      const reader = new FileReader();
      reader.onload = function (e) {
        const existingImg = document.querySelector('.h-16.w-16.rounded-full');
        if (existingImg.tagName === 'IMG') {
          existingImg.src = e.target.result;
        } else {
          // Replace the placeholder div with an image
          const newImg = document.createElement('img');
          newImg.className = 'h-16 w-16 rounded-full object-cover';
          newImg.src = e.target.result;
          newImg.alt = 'New profile image';
          existingImg.parentNode.replaceChild(newImg, existingImg);
        }
      };
      reader.readAsDataURL(e.target.files[0]);
    }
  });
}

// Auto-save functionality (optional)
let saveTimeout;
const formInputs = document.querySelectorAll('input, textarea, select');
formInputs.forEach((input) => {
  input.addEventListener('change', function () {
    clearTimeout(saveTimeout);
    // Optional: Show "saving..." indicator
    saveTimeout = setTimeout(() => {
      // Optional: Auto-save functionality can be implemented here
    }, 2000);
  });
});
