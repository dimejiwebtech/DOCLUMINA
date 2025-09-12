// Select all functionality
document.getElementById('select-all').addEventListener('change', function () {
  const checkboxes = document.querySelectorAll('.comment-checkbox');
  checkboxes.forEach((cb) => (cb.checked = this.checked));
});

// Show/hide action links on hover (desktop only)
document.querySelectorAll('.comment-row').forEach((row) => {
  const actionLinks = row.querySelector('.action-links');
  if (actionLinks) {
    row.addEventListener('mouseenter', () => {
      actionLinks.classList.remove('hidden');
    });

    row.addEventListener('mouseleave', () => {
      actionLinks.classList.add('hidden');
    });
  }
});

// Reply functionality
document.querySelectorAll('.reply-btn').forEach((btn) => {
  btn.addEventListener('click', function () {
    const commentId = this.dataset.commentId;
    const replyForm = document.querySelector(`.reply-form-${commentId}`);
    replyForm.classList.toggle('hidden');
  });
});

// Cancel reply
document.querySelectorAll('.cancel-reply').forEach((btn) => {
  btn.addEventListener('click', function () {
    const commentId = this.dataset.commentId;
    const replyForm = document.querySelector(`.reply-form-${commentId}`);
    replyForm.classList.add('hidden');
    replyForm.querySelector('textarea').value = '';
  });
});

// Edit functionality
document.querySelectorAll('.edit-btn').forEach((btn) => {
  btn.addEventListener('click', function () {
    const commentId = this.dataset.commentId;
    const commentBody = this.dataset.commentBody;

    document.getElementById('edit-comment-body').value = commentBody;
    document.getElementById(
      'edit-form'
    ).action = `/comments/${commentId}/edit/`;
    document.getElementById('edit-modal').classList.remove('hidden');
  });
});

// Cancel edit
document.getElementById('cancel-edit').addEventListener('click', () => {
  document.getElementById('edit-modal').classList.add('hidden');
});

// Close modal on background click
document.getElementById('edit-modal').addEventListener('click', function (e) {
  if (e.target === this) {
    this.classList.add('hidden');
  }
});
