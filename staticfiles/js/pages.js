// Select all functionality
document.getElementById('select-all').addEventListener('change', function () {
  const checkboxes = document.querySelectorAll('.page-checkbox');
  checkboxes.forEach((checkbox) => {
    checkbox.checked = this.checked;
  });
});

// Update select all checkbox based on individual selections
document.addEventListener('change', function (e) {
  if (e.target.matches('.page-checkbox')) {
    const allCheckboxes = document.querySelectorAll('.page-checkbox');
    const checkedCheckboxes = document.querySelectorAll(
      '.page-checkbox:checked'
    );
    const selectAllCheckbox = document.getElementById('select-all');

    selectAllCheckbox.checked =
      allCheckboxes.length === checkedCheckboxes.length;
    selectAllCheckbox.indeterminate =
      checkedCheckboxes.length > 0 &&
      checkedCheckboxes.length < allCheckboxes.length;
  }
});

// Bulk action form validation and submission
document
  .getElementById('bulk-action-form')
  .addEventListener('submit', function (e) {
    e.preventDefault();

    const action = this.querySelector('select[name="action"]').value;
    const selectedPages = document.querySelectorAll('.page-checkbox:checked');

    if (!action) {
      alert('Please select an action.');
      return;
    }

    if (selectedPages.length === 0) {
      alert('Please select at least one page.');
      return;
    }

    let actionText = action;
    if (action === 'delete') actionText = 'move to trash';
    else if (action === 'delete_permanently') actionText = 'permanently delete';

    const confirmMessage = `Are you sure you want to ${actionText} ${
      selectedPages.length
    } page${selectedPages.length > 1 ? 's' : ''}?`;

    if (!confirm(confirmMessage)) {
      return;
    }

    // Submit form via AJAX to handle redirect properly
    const formData = new FormData(this);
    const formAction = this.getAttribute('action');

    fetch(formAction, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')
          .value,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Redirect to maintain current status
          const currentStatus = document.querySelector(
            '[name="current_status"]'
          ).value;
          window.location.href = `?status=${currentStatus}`;
        } else {
          alert('Error: ' + (data.message || 'Something went wrong'));
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        alert('An error occurred while processing the request.');
      });
  });

// Delete page function
function deletePage(pageId) {
  if (confirm('Are you sure you want to move this page to trash?')) {
    fetch(`/dashboard/pages/delete-page/${pageId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')
          .value,
        'Content-Type': 'application/json',
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          location.reload();
        } else {
          alert('Error: ' + (data.message || 'Something went wrong'));
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        alert('An error occurred while deleting the page.');
      });
  }
}

// Restore page function
function restorePage(pageId) {
  if (confirm('Are you sure you want to restore this page?')) {
    fetch(`/dashboard/pages/restore-page/${pageId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')
          .value,
        'Content-Type': 'application/json',
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          location.reload();
        } else {
          alert('Error: ' + (data.message || 'Something went wrong'));
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        alert('An error occurred while restoring the page.');
      });
  }
}
