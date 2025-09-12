// Select all functionality
document.getElementById('select-all').addEventListener('change', function () {
  const checkboxes = document.querySelectorAll('input[name="post_ids"]');
  checkboxes.forEach((checkbox) => {
    checkbox.checked = this.checked;
  });
});

// Sync action selects between desktop and mobile
const actionSelects = document.querySelectorAll('select[name="action"]');
actionSelects.forEach((select) => {
  select.addEventListener('change', function () {
    actionSelects.forEach((otherSelect) => {
      if (otherSelect !== this) {
        otherSelect.value = this.value;
      }
    });
  });
});

// Bulk form validation with loading state
document.getElementById('bulk-form').addEventListener('submit', function (e) {
  const actionSelects = document.querySelectorAll('select[name="action"]');
  let action = '';

  actionSelects.forEach((select) => {
    if (select.value) {
      action = select.value;
    }
  });

  const checkedBoxes = document.querySelectorAll(
    'input[name="post_ids"]:checked'
  );

  if (!action) {
    e.preventDefault();
    alert('Please select an action.');
    return;
  }

  if (checkedBoxes.length === 0) {
    e.preventDefault();
    alert('Please select at least one post.');
    return;
  }

  if (action === 'delete') {
    if (
      !confirm(
        'Are you sure you want to permanently delete these posts? This action cannot be undone.'
      )
    ) {
      e.preventDefault();
      return;
    }
  }

  // Add loading state
  const submitButtons = document.querySelectorAll(
    'button[type="submit"][form="bulk-form"], button[type="submit"]:not([form])'
  );
  submitButtons.forEach((button) => {
    button.disabled = true;
    button.innerHTML = 'Processing...';
  });
});
