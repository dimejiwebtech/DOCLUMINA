document.addEventListener('DOMContentLoaded', function () {
  // Get elements
  const mediaGrid = document.getElementById('media-grid');
  const mediaModal = document.getElementById('media-modal');
  const modalOverlay = document.getElementById('modal-overlay');
  const closeModal = document.getElementById('close-modal');
  const loadMoreBtn = document.getElementById('load-more-btn');
  const bulkSelectBtn = document.getElementById('bulk-select-btn');
  const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
  const mediaTypeFilter = document.getElementById('media-type-filter');
  const dateFilter = document.getElementById('date-filter');
  const searchInput = document.getElementById('search-input');

  // Upload elements
  const addMediaBtn = document.getElementById('add-media-btn');
  const uploadBox = document.getElementById('upload-box');
  const closeUploadBtn = document.getElementById('close-upload-btn');
  const uploadForm = document.getElementById('upload-form');
  const fileInput = document.getElementById('file-input');
  const uploadSubmitBtn = document.getElementById('upload-submit-btn');
  const uploadProgress = document.getElementById('upload-progress');
  const progressBar = document.getElementById('progress-bar');
  const uploadStatus = document.getElementById('upload-status');
  const uploadFirstBtn = document.getElementById('upload-first-btn');

  let bulkSelectMode = false;
  let selectedMedia = new Set();

  // Show/hide upload box
  addMediaBtn.addEventListener('click', function () {
    uploadBox.classList.toggle('hidden');
  });

  if (uploadFirstBtn) {
    uploadFirstBtn.addEventListener('click', function () {
      uploadBox.classList.remove('hidden');
    });
  }

  closeUploadBtn.addEventListener('click', function () {
    uploadBox.classList.add('hidden');
    resetUploadForm();
  });

  // File input handling
  fileInput.addEventListener('change', function () {
    const hasFiles = this.files.length > 0;
    uploadSubmitBtn.disabled = !hasFiles;

    if (hasFiles) {
      uploadSubmitBtn.textContent = `Upload ${this.files.length} file(s)`;
    } else {
      uploadSubmitBtn.textContent = 'Upload Files';
    }
  });

  // Drag and drop
  const dropZone = uploadBox.querySelector('.border-dashed');

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach((eventName) => {
    dropZone.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach((eventName) => {
    dropZone.addEventListener(eventName, unhighlight, false);
  });

  function highlight(e) {
    dropZone.classList.add('border-blue-400', 'bg-blue-50');
  }

  function unhighlight(e) {
    dropZone.classList.remove('border-blue-400', 'bg-blue-50');
  }

  dropZone.addEventListener('drop', handleDrop, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    fileInput.files = files;

    const hasFiles = files.length > 0;
    uploadSubmitBtn.disabled = !hasFiles;

    if (hasFiles) {
      uploadSubmitBtn.textContent = `Upload ${files.length} file(s)`;
    }
  }

  // Upload form submission
  uploadForm.addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData();
    const files = fileInput.files;

    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    // Add CSRF token
    const csrfToken = document.querySelector(
      '[name=csrfmiddlewaretoken]'
    )?.value;
    if (csrfToken) {
      formData.append('csrfmiddlewaretoken', csrfToken);
    }

    // Show progress
    uploadProgress.classList.remove('hidden');
    uploadSubmitBtn.disabled = true;
    uploadSubmitBtn.textContent = 'Uploading...';

    fetch('/dashboard/media/add-media/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotification(data.message, 'success');

          // Add new files to grid
          data.files.forEach((media) => {
            const mediaElement = createMediaElement(media);
            mediaGrid.appendChild(mediaElement);
          });

          resetUploadForm();
          uploadBox.classList.add('hidden');
        } else {
          showNotification('Upload failed', 'error');
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        showNotification('Upload failed', 'error');
      })
      .finally(() => {
        uploadProgress.classList.add('hidden');
        uploadSubmitBtn.disabled = false;
        uploadSubmitBtn.textContent = 'Upload Files';
      });
  });

  function resetUploadForm() {
    uploadForm.reset();
    uploadSubmitBtn.disabled = true;
    uploadSubmitBtn.textContent = 'Upload Files';
    uploadProgress.classList.add('hidden');
    progressBar.style.width = '0%';
  }

  // Media item click handler
  mediaGrid.addEventListener('click', function (e) {
    const mediaItem = e.target.closest('.media-item');
    if (
      mediaItem &&
      !bulkSelectMode &&
      !e.target.classList.contains('media-checkbox')
    ) {
      const mediaId = mediaItem.dataset.mediaId;
      openMediaModal(mediaId);
    }
  });

  // Open media modal
  function openMediaModal(mediaId) {
    fetch(`/dashboard/media/${mediaId}/`, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then((response) => response.json())
      .then((data) => {
        populateModal(data);
        mediaModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
      })
      .catch((error) => {
        console.error('Error:', error);
        showNotification('Error loading media details', 'error');
      });
  }

  // Populate modal with media data
  function populateModal(data) {
    const preview = document.getElementById('modal-preview');
    const info = document.getElementById('media-info');

    // Set preview
    if (data.type === 'image') {
      preview.innerHTML = `<img src="${data.url}" alt="${data.alt_text}" class="max-w-full max-h-[400px] object-contain rounded mx-auto">`;
      document.getElementById('edit-image-btn').classList.remove('hidden');
    } else {
      const iconClass = getFileIconClass(data.type);
      preview.innerHTML = `
                <div class="text-center">
                    <div class="text-8xl text-gray-400 mb-4">
                        <i class="${iconClass}"></i>
                    </div>
                    <p class="text-lg font-medium text-gray-700">${
                      data.name
                    }</p>
                    <p class="text-sm text-gray-500">${
                      data.file_extension || ''
                    }</p>
                </div>
            `;
      document.getElementById('edit-image-btn').classList.add('hidden');
    }

    // Set info
    info.innerHTML = `
            <p><strong>Uploaded on:</strong> ${data.created_at}</p>
            <p><strong>File name:</strong> ${data.name}</p>
            <p><strong>File type:</strong> ${data.type}</p>
            <p><strong>File size:</strong> ${data.size}</p>
        `;

    // Set form values
    document.getElementById('alt-text-input').value = data.alt_text || '';
    document.getElementById('description-input').value = data.description || '';
    document.getElementById('file-url-input').value = data.url;

    // Store media ID for updates
    document.getElementById('media-update-form').dataset.mediaId = data.id;
  }

  // Get file icon class
  function getFileIconClass(type) {
    const icons = {
      document: 'fas fa-file-alt',
      video: 'fas fa-video',
      audio: 'fas fa-music',
      spreadsheet: 'fas fa-file-excel',
      other: 'fas fa-file',
    };
    return icons[type] || 'fas fa-file';
  }

  // Close modal handlers
  closeModal.addEventListener('click', closeMediaModal);
  modalOverlay.addEventListener('click', closeMediaModal);

  function closeMediaModal() {
    mediaModal.classList.add('hidden');
    document.body.style.overflow = '';
  }

  // Create media element
  function createMediaElement(media) {
    const div = document.createElement('div');
    div.className =
      'media-item group relative bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow cursor-pointer';
    div.dataset.mediaId = media.id;

    let preview = '';
    if (media.type === 'image') {
      preview = `<img src="${media.url}" alt="${
        media.alt_text || ''
      }" class="w-full h-full object-cover">`;
    } else {
      const iconClass = getFileIconClass(media.type);
      preview = `
                <div class="w-full h-full flex items-center justify-center text-2xl text-gray-400">
                    <i class="${iconClass}"></i>
                </div>
                ${
                  media.file_extension
                    ? `<div class="absolute bottom-1 right-1 bg-black bg-opacity-75 text-white text-xs px-1 py-0.5 rounded">${media.file_extension}</div>`
                    : ''
                }
            `;
    }

    div.innerHTML = `
            <!-- Selection Checkbox (hidden by default) -->
            <div class="absolute top-1 left-1 z-10 opacity-0 group-hover:opacity-100 transition-opacity bulk-select-checkbox hidden">
                <input type="checkbox" class="media-checkbox w-3 h-3 text-blue-600 bg-white border-gray-300 rounded focus:ring-blue-500" value="${
                  media.id
                }">
            </div>

            <!-- Media Preview -->
            <div class="aspect-square relative overflow-hidden bg-gray-100">
                ${preview}
            </div>

            <!-- Media Info -->
            <div class="p-2">
                <p class="text-xs font-medium text-gray-900 truncate" title="${
                  media.name
                }">
                    ${
                      media.name.length > 15
                        ? media.name.substring(0, 15) + '...'
                        : media.name
                    }
                </p>
                <p class="text-xs text-gray-500 mt-0.5">${media.size}</p>
            </div>
        `;

    return div;
  }

  // Bulk select functionality
  bulkSelectBtn.addEventListener('click', function () {
    bulkSelectMode = !bulkSelectMode;
    const checkboxes = document.querySelectorAll('.bulk-select-checkbox');

    if (bulkSelectMode) {
      this.textContent = 'Cancel';
      this.classList.add('bg-gray-600', 'text-white');
      this.classList.remove('border-gray-300', 'hover:bg-gray-50');
      checkboxes.forEach((cb) => cb.classList.remove('hidden'));
      bulkDeleteBtn.classList.remove('hidden');
    } else {
      this.textContent = 'Bulk select';
      this.classList.remove('bg-gray-600', 'text-white');
      this.classList.add('border-gray-300', 'hover:bg-gray-50');
      checkboxes.forEach((cb) => {
        cb.classList.add('hidden');
        cb.querySelector('input').checked = false;
      });
      bulkDeleteBtn.classList.add('hidden');
      selectedMedia.clear();
    }
  });

  // Handle checkbox changes
  mediaGrid.addEventListener('change', function (e) {
    if (e.target.classList.contains('media-checkbox')) {
      const mediaId = e.target.value;
      if (e.target.checked) {
        selectedMedia.add(mediaId);
      } else {
        selectedMedia.delete(mediaId);
      }

      const count = selectedMedia.size;
      bulkDeleteBtn.textContent =
        count > 0 ? `Delete Selected (${count})` : 'Delete Selected';
    }
  });

  // Bulk delete functionality
  bulkDeleteBtn.addEventListener('click', function () {
    if (selectedMedia.size === 0) return;

    if (
      confirm(
        `Are you sure you want to delete ${selectedMedia.size} selected media file(s)? This action cannot be undone.`
      )
    ) {
      fetch('/dashboard/media/bulk-delete/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          media_ids: Array.from(selectedMedia),
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            selectedMedia.forEach((mediaId) => {
              const mediaItem = document.querySelector(
                `[data-media-id="${mediaId}"]`
              );
              if (mediaItem) {
                mediaItem.remove();
              }
            });

            selectedMedia.clear();
            bulkSelectBtn.click(); // Exit bulk select mode
            showNotification(data.message, 'success');
          } else {
            showNotification('Error deleting files', 'error');
          }
        })
        .catch((error) => {
          console.error('Error:', error);
          showNotification('Error deleting files', 'error');
        });
    }
  });

  // Filter functionality
  function applyFilters() {
    const type = mediaTypeFilter.value;
    const date = dateFilter.value;
    const search = searchInput.value;

    const url = new URL(window.location);
    url.searchParams.set('type', type);
    url.searchParams.set('date', date);
    url.searchParams.set('search', search);
    url.searchParams.delete('page'); // Reset pagination

    window.location.href = url.toString();
  }

  mediaTypeFilter.addEventListener('change', applyFilters);
  dateFilter.addEventListener('change', applyFilters);

  // Search with debounce
  let searchTimeout;
  searchInput.addEventListener('input', function () {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(applyFilters, 500);
  });

  // Load more functionality
if (loadMoreBtn) {
  loadMoreBtn.addEventListener('click', function () {
    const nextPage = this.dataset.nextPage;
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('page', nextPage);

    fetch(currentUrl.toString(), {
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then((response) => response.json())
      .then((data) => {
        data.media_files.forEach((media) => {
          const mediaElement = createMediaElement(media);
          mediaGrid.appendChild(mediaElement); // Changed from insertBefore
        });

        if (data.has_next) {
          this.dataset.nextPage = data.next_page_number;
        } else {
          this.style.display = 'none';
        }
      })
      .catch((error) => console.error('Error:', error));
  });
}

  // Media update form
  document
    .getElementById('media-update-form')
    .addEventListener('submit', function (e) {
      e.preventDefault();

      const mediaId = this.dataset.mediaId;
      const formData = {
        alt_text: document.getElementById('alt-text-input').value,
        description: document.getElementById('description-input').value,
      };

      fetch(`/dashboard/media/${mediaId}/update/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(formData),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            showNotification(data.message, 'success');
            closeMediaModal();
          } else {
            showNotification('Error updating media', 'error');
          }
        })
        .catch((error) => {
          console.error('Error:', error);
          showNotification('Error updating media', 'error');
        });
    });

  // Delete media
  document
    .getElementById('delete-media-btn')
    .addEventListener('click', function () {
      const mediaId =
        document.getElementById('media-update-form').dataset.mediaId;

      if (
        confirm(
          'Are you sure you want to delete this media file? This action cannot be undone.'
        )
      ) {
        fetch(`/dashboard/media/${mediaId}/delete/`, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(),
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              const mediaItem = document.querySelector(
                `[data-media-id="${mediaId}"]`
              );
              if (mediaItem) {
                mediaItem.remove();
              }

              closeMediaModal();
              showNotification(data.message, 'success');
            } else {
              showNotification('Error deleting media', 'error');
            }
          })
          .catch((error) => {
            console.error('Error:', error);
            showNotification('Error deleting media', 'error');
          });
      }
    });

  // Copy URL functionality
  document
    .getElementById('copy-url-btn')
    .addEventListener('click', function () {
      const urlInput = document.getElementById('file-url-input');
      urlInput.select();
      navigator.clipboard
        .writeText(urlInput.value)
        .then(() => {
          const originalText = this.textContent;
          this.textContent = 'Copied!';
          this.classList.add('bg-green-600');
          this.classList.remove('bg-blue-600', 'hover:bg-blue-700');

          setTimeout(() => {
            this.textContent = originalText;
            this.classList.remove('bg-green-600');
            this.classList.add('bg-blue-600', 'hover:bg-blue-700');
          }, 2000);
        })
        .catch(() => {
          // Fallback for older browsers
          urlInput.select();
          document.execCommand('copy');
          showNotification('URL copied to clipboard', 'success');
        });
    });

  // Utility functions
  function getCsrfToken() {
    return (
      document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
      document
        .querySelector('meta[name=csrf-token]')
        ?.getAttribute('content') ||
      ''
    );
  }

  function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');

    const bgColor =
      type === 'success'
        ? 'bg-green-100 border-green-500 text-green-800'
        : type === 'error'
        ? 'bg-red-100 border-red-500 text-red-800'
        : 'bg-blue-100 border-blue-500 text-blue-800';

    const icon =
      type === 'success'
        ? 'fa-check-circle'
        : type === 'error'
        ? 'fa-exclamation-circle'
        : 'fa-info-circle';

    notification.className = `max-w-sm p-4 rounded-lg shadow-lg border-l-4 ${bgColor} transform translate-x-full transition-transform duration-300`;

    notification.innerHTML = `
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium">${message}</p>
                </div>
                <div class="ml-auto pl-3">
                    <button class="text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

    container.appendChild(notification);

    // Animate in
    setTimeout(() => {
      notification.classList.remove('translate-x-full');
    }, 100);

    // Auto remove after 5 seconds
    setTimeout(() => {
      notification.classList.add('translate-x-full');
      setTimeout(() => {
        if (notification.parentElement) {
          notification.remove();
        }
      }, 300);
    }, 5000);
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', function (e) {
    // Escape key to close modal or upload box
    if (e.key === 'Escape') {
      if (!mediaModal.classList.contains('hidden')) {
        closeMediaModal();
      } else if (!uploadBox.classList.contains('hidden')) {
        uploadBox.classList.add('hidden');
        resetUploadForm();
      }
    }

    // Ctrl/Cmd + A to select all in bulk mode
    if ((e.ctrlKey || e.metaKey) && e.key === 'a' && bulkSelectMode) {
      e.preventDefault();
      const checkboxes = document.querySelectorAll('.media-checkbox input');
      checkboxes.forEach((cb) => {
        if (!cb.checked) {
          cb.checked = true;
          selectedMedia.add(cb.value);
        }
      });

      const count = selectedMedia.size;
      bulkDeleteBtn.textContent =
        count > 0 ? `Delete Selected (${count})` : 'Delete Selected';
    }
  });

  // Handle mobile menu toggle
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', function () {
      const sidebar = document.querySelector('.sidebar');
      if (sidebar) {
        sidebar.classList.toggle('-translate-x-full');
      }
    });
  }
});
