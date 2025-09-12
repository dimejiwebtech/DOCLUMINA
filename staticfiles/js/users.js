document.addEventListener('DOMContentLoaded', function () {
  // Get DOM elements
  const selectAllCheckbox = document.getElementById('select-all');
  const userCheckboxes = document.querySelectorAll(
    'input[name="user_checkbox"]'
  );
  const applyBtn = document.getElementById('apply-btn');
  const searchInput = document.querySelector('input[name="search"]');
  const editModal = document.getElementById('edit-modal');

  // Select all checkbox functionality
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', function () {
      userCheckboxes.forEach((cb) => (cb.checked = this.checked));
      updateBulkActions();
    });
  }

  // Individual checkbox functionality
  userCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', updateBulkActions);
  });

  function updateBulkActions() {
    const checkedBoxes = document.querySelectorAll(
      'input[name="user_checkbox"]:checked'
    );
    const selectedUsers = Array.from(checkedBoxes).map((cb) => cb.value);

    // Update hidden input
    const hiddenInput = document.querySelector('#id_selected_users');
    if (hiddenInput) {
      hiddenInput.value = JSON.stringify(selectedUsers);
    }

    // Enable/disable apply button
    if (applyBtn) {
      applyBtn.disabled = selectedUsers.length === 0;
    }

    // Update select all checkbox state
    if (selectAllCheckbox) {
      selectAllCheckbox.checked = checkedBoxes.length === userCheckboxes.length;
      selectAllCheckbox.indeterminate =
        checkedBoxes.length > 0 && checkedBoxes.length < userCheckboxes.length;
    }
  }

  // Auto-submit search form
  let searchTimeout;
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        this.form.submit();
      }, 300);
    });
  }

  // Close modal when clicking outside
  if (editModal) {
    editModal.addEventListener('click', function (e) {
      if (e.target === this) {
        closeModal();
      }
    });
  }
});

// Edit user modal
function editUser(userId) {
  fetch(`/dashboard/users/${userId}/edit/`, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
    .then((response) => {
      if (!response.ok) throw new Error('Network response was not ok');
      return response.text();
    })
    .then((html) => {
      document.getElementById('modal-content').innerHTML = html;
      document.getElementById('edit-modal').classList.remove('hidden');
    })
    .catch((error) => {
      console.error('Error:', error);
      alert('Error loading user data');
    });
}

function closeModal() {
  const modal = document.getElementById('edit-modal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

// Delete user
function deleteUser(userId, username) {
  if (confirm(`Are you sure you want to delete user "${username}"?`)) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
      alert('CSRF token not found');
      return;
    }

    fetch(`/dashboard/users/${userId}/delete/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken.value,
        'Content-Type': 'application/json',
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          location.reload();
        } else {
          alert(data.message || 'Error deleting user');
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        alert('Error deleting user');
      });
  }
}
