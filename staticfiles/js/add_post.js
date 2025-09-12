class PostEditor {
  constructor() {
    this.postId = window.djangoData ? window.djangoData.postId : null;
    this.autoSaveTimeout = null;
    this.slugTimeout = null;
    this.originalSlug = '';
    this.init();
  }

  init() {
    this.bindEvents();
    this.initCharCounter();
    this.initPermalink();
  }

  bindEvents() {
    // Title input for permalink generation
    const titleInput = document.getElementById('id_title');
    if (titleInput) {
      titleInput.addEventListener('input', () => {
        this.handleTitleChange();
        this.scheduleAutoSave();
      });
    }

    // Featured image handling
    const featuredImageInput = document.getElementById('id_featured_image');
    if (featuredImageInput) {
      featuredImageInput.addEventListener(
        'change',
        this.handleImageChange.bind(this)
      );
    }

    // Auto-save for all inputs
    const autoSaveFields = [
      'id_content',
      'id_excerpt',
      'id_seo_description',
      'id_seo_keywords',
      'id_slug',
    ];
    autoSaveFields.forEach((fieldId) => {
      const field = document.getElementById(fieldId);
      if (field) {
        field.addEventListener('input', () => this.scheduleAutoSave());
      }
    });

    document.querySelectorAll('input[name="category"]').forEach((checkbox) => {
      checkbox.addEventListener('change', () => this.scheduleAutoSave());
    });

    const seoInput = document.getElementById('id_seo_description');
    if (seoInput) {
      seoInput.addEventListener('input', this.updateCharCounter.bind(this));
    }

    // CKEditor5 content change detection
    const checkForEditor = setInterval(() => {
      // Check for CKEditor5 (newer approach)
      if (window.ClassicEditor || window.CKEDITOR) {
        // Try CKEditor5 first
        const editorElement = document.querySelector('.ck-editor__editable');
        if (editorElement) {
          // Use MutationObserver to detect content changes
          const observer = new MutationObserver(() => {
            this.scheduleAutoSave();
          });
          observer.observe(editorElement, {
            childList: true,
            subtree: true,
            characterData: true,
          });
          clearInterval(checkForEditor);
        }
        // Fallback to classic CKEditor
        else if (window.CKEDITOR && window.CKEDITOR.instances) {
          for (let instanceName in window.CKEDITOR.instances) {
            const editor = window.CKEDITOR.instances[instanceName];
            editor.on('change', () => this.scheduleAutoSave());
          }
          clearInterval(checkForEditor);
        }
      }
    }, 1000);
  }

  handleTitleChange() {
    const titleInput = document.getElementById('id_title');
    const permalinkSection = document.getElementById('permalink-section');

    if (titleInput.value.trim()) {
      permalinkSection.classList.remove('hidden');

      if (!this.isSlugManuallyEdited()) {
        clearTimeout(this.slugTimeout);
        this.slugTimeout = setTimeout(() => this.generateSlug(), 10000);
      }
    } else {
      permalinkSection.classList.add('hidden');
    }
  }

  isSlugManuallyEdited() {
    const slugInput = document.getElementById('id_slug');
    const titleInput = document.getElementById('id_title');
    if (!slugInput || !titleInput) return false;

    // Simple check: if slug doesn't match title pattern, it's manually edited
    const titleSlug = this.slugify(titleInput.value);
    return slugInput.value !== titleSlug && slugInput.value !== '';
  }

  slugify(text) {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  generateSlug() {
    const titleInput = document.getElementById('id_title');
    const slugDisplay = document.getElementById('slug-display');

    if (!titleInput.value) return;

    fetch(
      `${window.djangoData.urls.generateSlug}?title=${encodeURIComponent(
        titleInput.value
      )}&post_id=${this.postId || ''}`
    )
      .then((response) => response.json())
      .then((data) => {
        if (data.slug) {
          document.getElementById('id_slug').value = data.slug;
          slugDisplay.textContent = data.slug;
        }
      })
      .catch((error) => console.error('Error generating slug:', error));
  }

  initPermalink() {
    const slugInput = document.getElementById('id_slug');
    if (slugInput) {
      this.originalSlug = slugInput.value;
    }
  }

  editPermalink() {
    const slugDisplay = document.getElementById('slug-display');
    const slugEdit = document.getElementById('slug-edit');
    const editBtn = document.getElementById('edit-slug-btn');
    const saveBtn = document.getElementById('save-slug-btn');
    const cancelBtn = document.getElementById('cancel-slug-btn');

    slugDisplay.classList.add('hidden');
    slugEdit.classList.remove('hidden');
    editBtn.classList.add('hidden');
    saveBtn.classList.remove('hidden');
    cancelBtn.classList.remove('hidden');

    document.getElementById('id_slug').focus();
  }

  savePermalink() {
    const slugInput = document.getElementById('id_slug');
    const slugDisplay = document.getElementById('slug-display');
    const slugEdit = document.getElementById('slug-edit');
    const editBtn = document.getElementById('edit-slug-btn');
    const saveBtn = document.getElementById('save-slug-btn');
    const cancelBtn = document.getElementById('cancel-slug-btn');

    this.originalSlug = slugInput.value;
    slugDisplay.textContent = slugInput.value;

    slugDisplay.classList.remove('hidden');
    slugEdit.classList.add('hidden');
    editBtn.classList.remove('hidden');
    saveBtn.classList.add('hidden');
    cancelBtn.classList.add('hidden');

    this.scheduleAutoSave();
  }

  cancelEditPermalink() {
    const slugInput = document.getElementById('id_slug');
    const slugDisplay = document.getElementById('slug-display');
    const slugEdit = document.getElementById('slug-edit');
    const editBtn = document.getElementById('edit-slug-btn');
    const saveBtn = document.getElementById('save-slug-btn');
    const cancelBtn = document.getElementById('cancel-slug-btn');

    slugInput.value = this.originalSlug;
    slugDisplay.textContent = this.originalSlug;

    slugDisplay.classList.remove('hidden');
    slugEdit.classList.add('hidden');
    editBtn.classList.remove('hidden');
    saveBtn.classList.add('hidden');
    cancelBtn.classList.add('hidden');
  }



  updateCharCounter() {
    const input = document.getElementById('id_seo_description');
    const counter = document.getElementById('seo-char-count');
    const warning = document.getElementById('seo-char-warning');

    if (!input || !counter) return;

    const length = input.value.length;
    counter.textContent = length;

    if (length > 160) {
      counter.classList.add('text-red-500', 'font-bold');
      counter.classList.remove('text-gray-500');
      warning.classList.remove('hidden');
    } else {
      counter.classList.remove('text-red-500', 'font-bold');
      counter.classList.add('text-gray-500');
      warning.classList.add('hidden');
    }
  }

  initCharCounter() {
    // Initialize character counter on page load
    this.updateCharCounter();
  }

  scheduleAutoSave() {
    clearTimeout(this.autoSaveTimeout);
    this.autoSaveTimeout = setTimeout(() => this.autoSave(), 3000);
  }

  autoSave() {
    const indicator = document.getElementById('autosave-indicator');
    indicator.classList.remove('hidden');

    const formData = this.collectFormData();

    fetch(window.djangoData.urls.autoSavePost, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')
          .value,
      },
      body: JSON.stringify(formData),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          if (!this.postId) {
            this.postId = data.post_id;
            // Update URL without refresh for new posts
            history.replaceState(
              null,
              '',
              `${window.djangoData.urls.editPostUrl}${this.postId}/`
            );
          }

          // Update slug display if changed
          if (data.slug) {
            document.getElementById('id_slug').value = data.slug;
            document.getElementById('slug-display').textContent = data.slug;
          }

          this.showSaveSuccess();
        } else {
          this.showSaveError();
        }
      })
      .catch((error) => {
        console.error('Auto-save failed:', error);
        this.showSaveError();
      });
  }

  collectFormData() {
    const data = {
      title: document.getElementById('id_title')?.value || '',
      slug: document.getElementById('id_slug')?.value || '',
      content: this.getCKEditorContent(),
      excerpt: document.getElementById('id_excerpt')?.value || '',
      seo_description:
        document.getElementById('id_seo_description')?.value || '',
      seo_keywords: document.getElementById('id_seo_keywords')?.value || '',
      category: Array.from(
        document.querySelectorAll('input[name="category"]:checked')
      ).map((cb) => cb.value),
    };

    // Include selected featured image from media library if present
    const selectedFeaturedImageId = document.getElementById(
      'selected-featured-image-id'
    );
    if (selectedFeaturedImageId) {
      data.featured_image_id = selectedFeaturedImageId.value;
    }

    if (this.postId) {
      data.post_id = this.postId;
    }

    return data;
  }

  getCKEditorContent() {
    // Try to get CKEditor content
    if (window.CKEDITOR && window.CKEDITOR.instances) {
      for (let instance in window.CKEDITOR.instances) {
        return window.CKEDITOR.instances[instance].getData();
      }
    }

    // Fallback to textarea value
    const contentField = document.getElementById('id_content');
    return contentField ? contentField.value : '';
  }

  showSaveSuccess() {
    const indicator = document.getElementById('autosave-indicator');
    indicator.innerHTML = `
            <div class="flex items-center text-sm">
                <svg class="w-4 h-4 mr-2 text-green-800" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                Saved
            </div>
        `;
    setTimeout(() => indicator.classList.add('hidden'), 2000);
  }

  showSaveError() {
    const indicator = document.getElementById('autosave-indicator');
    indicator.innerHTML = `
            <div class="flex items-center text-sm bg-red-100 text-red-800">
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
                Save failed
            </div>
        `;
    setTimeout(() => indicator.classList.add('hidden'), 3000);
  }
}

// Global functions for template buttons
function editPermalink() {
  postEditor.editPermalink();
}

function savePermalink() {
  postEditor.savePermalink();
}

function cancelEditPermalink() {
  postEditor.cancelEditPermalink();
}

function removeFeaturedImage() {
  if (!confirm('Are you sure you want to remove the featured image?')) return;

  const preview = document.getElementById('featured-image-preview');
  const nameDisplay = document.getElementById('featured-image-name'); // Updated ID
  const hiddenInput = document.getElementById('selected-featured-image-id');

  // Clear values
  if (hiddenInput) hiddenInput.value = '';
  if (nameDisplay) nameDisplay.textContent = 'No image selected'; // Updated text
  if (preview) preview.classList.add('hidden');

  // Remove from server if editing existing post
  if (postEditor.postId) {
    fetch(window.djangoData.urls.removeFeaturedImage, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.djangoData.csrfToken,
      },
      body: JSON.stringify({ post_id: postEditor.postId }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          console.log('Featured image removed successfully');
        }
      })
      .catch((error) => console.error('Error removing featured image:', error));
  }

  // Trigger autosave
  postEditor.scheduleAutoSave();
}

function previewPost() {
  if (postEditor.postId) {
    // Preview will handle published vs draft logic on the server side
    window.open(`/dashboard/post-preview/${postEditor.postId}/`, '_blank');
  } else {
    alert('Please save the post first to preview it.');
  }
}

function openMediaLibrary(context = 'editor') {
  // Store the context globally so other functions can access it
  window.mediaLibraryContext = context;
  createMediaLibraryModal();
}

function createMediaLibraryModal() {
  // Create modal HTML
  const modalHTML = `
        <div id="media-library-modal" class="fixed inset-0 z-50">
            <div class="fixed inset-0 bg-transparent bg-opacity-50 transition-opacity"></div>
            <div class="flex items-center justify-center min-h-screen px-4 py-8">
                <div class="relative bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
                    <div class="flex items-center justify-between p-4 border-b border-gray-200">
                        <h3 class="text-lg font-medium text-gray-900">Media Library</h3>
                        <div class="flex items-center gap-2">
                            <button id="upload-media-btn" class="inline-flex items-center px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
                                <i class="fas fa-plus mr-2"></i>
                                Upload Media
                            </button>
                            <button id="close-media-library" class="text-gray-400 hover:text-gray-600 text-2xl">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Upload Box (Hidden by default) -->
                    <div id="modal-upload-box" class="hidden bg-gray-50 border-b border-gray-200 p-4">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="text-md font-medium text-gray-900">Upload Files</h4>
                            <button id="close-modal-upload" class="text-gray-400 hover:text-gray-600">
                                <i class="fas fa-times text-lg"></i>
                            </button>
                        </div>
                        
                        <form id="modal-upload-form" enctype="multipart/form-data">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${
                              document.querySelector(
                                '[name=csrfmiddlewaretoken]'
                              )?.value || ''
                            }">
                            <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                                <div class="mb-3">
                                    <i class="fas fa-cloud-upload-alt text-3xl text-gray-400"></i>
                                </div>
                                <div class="mb-3">
                                    <label for="modal-file-input" class="cursor-pointer">
                                        <span class="text-md font-medium text-gray-700">Drop files here or click to browse</span>
                                        <input type="file" id="modal-file-input" name="files" multiple class="hidden" accept="*/*">
                                    </label>
                                </div>
                                <p class="text-sm text-gray-500">Support for a single or bulk upload</p>
                            </div>
                            
                            <div class="mt-3 flex justify-end">
                                <button type="submit" id="modal-upload-submit" disabled
                                        class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors">
                                    Upload Files
                                </button>
                            </div>
                        </form>
                        
                        <!-- Upload Progress -->
                        <div id="modal-upload-progress" class="hidden mt-3">
                            <div class="bg-gray-200 rounded-full h-2">
                                <div id="modal-progress-bar" class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                            </div>
                            <p id="modal-upload-status" class="text-sm text-gray-600 mt-2">Uploading...</p>
                        </div>
                    </div>

                    <div class="p-4 overflow-y-auto" style="max-height: 60vh;">
                        <div id="media-library-content" class="min-h-[400px]">
                            <div class="flex items-center justify-center h-32">
                                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                                <span class="ml-2">Loading media library...</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
                        <div class="text-sm text-gray-600">
                            <span id="media-library-instruction">Select an image to insert into your post</span>
                        </div>
                        <button id="insert-selected-media" disabled class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed">
                            <span id="insert-button-text">Insert Selected</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

  // Add modal to page
  document.body.insertAdjacentHTML('beforeend', modalHTML);
  document.body.style.overflow = 'hidden';

  // Load media library content
  loadMediaLibraryContent();

  // Bind events
  bindMediaLibraryEvents();
}

function loadMediaLibraryContent() {
  fetch('/dashboard/media/?post-editor=1', {
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
    .then((response) => response.json())
    .then((data) => {
      // Build the grid HTML from JSON data
      let gridHTML = '';

      if (data.media_files && data.media_files.length > 0) {
        data.media_files.forEach((media) => {
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

          gridHTML += `
                    <div class="media-item group relative bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow cursor-pointer" data-media-id="${
                      media.id
                    }">
                        <div class="aspect-square relative overflow-hidden bg-gray-100">
                            ${preview}
                        </div>
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
                            <p class="text-xs text-gray-500 mt-0.5">${
                              media.size
                            }</p>
                        </div>
                    </div>
                `;
        });
      } else {
        gridHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-gray-400 text-6xl mb-4">
                        <i class="fas fa-folder-open"></i>
                    </div>
                    <p class="text-gray-500 text-lg">No media files found</p>
                </div>
            `;
      }

      document.getElementById('media-library-content').innerHTML = `
            <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
                ${gridHTML}
            </div>
        `;

      // Update UI based on context
      const instruction = document.getElementById('media-library-instruction');
      const buttonText = document.getElementById('insert-button-text');

      if (window.mediaLibraryContext === 'featured-image') {
        instruction.textContent = 'Select an image to use as featured image';
        buttonText.textContent = 'Set Featured Image';
      } else {
        instruction.textContent = 'Select an image to insert into your post';
        buttonText.textContent = 'Insert Selected';
      }

      // Make media items selectable
      makeMediaItemsSelectable();
    })
    .catch((error) => {
      console.error('Error loading media library:', error);
      document.getElementById('media-library-content').innerHTML = `
            <div class="text-center text-red-600">
                <p>Error loading media library. Please try again.</p>
            </div>
        `;
    });
}

let selectedMediaItem = null;

function makeMediaItemsSelectable() {
  const mediaItems = document.querySelectorAll(
    '#media-library-modal .media-item'
  );
  const insertButton = document.getElementById('insert-selected-media');

  mediaItems.forEach((item) => {
    item.addEventListener('click', function () {
      // For featured image, only allow images
      if (window.mediaLibraryContext === 'featured-image') {
        const img = this.querySelector('img');
        if (!img) {
          alert('Please select an image file for the featured image.');
          return;
        }
      }

      // Remove previous selection
      mediaItems.forEach((i) => i.classList.remove('ring-4', 'ring-blue-500'));

      // Add selection to clicked item
      this.classList.add('ring-4', 'ring-blue-500');

      // Store selected media
      selectedMediaItem = {
        id: this.dataset.mediaId,
        url: this.querySelector('img')?.src || '',
        alt: this.querySelector('img')?.alt || '',
        name: this.querySelector('p')?.textContent || '',
      };

      // Enable insert button
      insertButton.disabled = false;
    });
  });
}

function bindMediaLibraryEvents() {
  // Close modal
  document
    .getElementById('close-media-library')
    .addEventListener('click', closeMediaLibrary);

  // Insert selected media (updated to handle both contexts)
  document
    .getElementById('insert-selected-media')
    .addEventListener('click', insertSelectedMedia);

  // Close on overlay click
  document
    .querySelector('#media-library-modal .fixed.inset-0')
    .addEventListener('click', closeMediaLibrary);

  // Upload media functionality
  const uploadBtn = document.getElementById('upload-media-btn');
  const uploadBox = document.getElementById('modal-upload-box');
  const closeUploadBtn = document.getElementById('close-modal-upload');
  const uploadForm = document.getElementById('modal-upload-form');
  const fileInput = document.getElementById('modal-file-input');
  const uploadSubmitBtn = document.getElementById('modal-upload-submit');

  // Show/hide upload box
  uploadBtn.addEventListener('click', function () {
    uploadBox.classList.toggle('hidden');
  });

  closeUploadBtn.addEventListener('click', function () {
    uploadBox.classList.add('hidden');
    resetModalUploadForm();
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
    const uploadProgress = document.getElementById('modal-upload-progress');
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
          // Add new files to modal grid
          const mediaGrid = document.querySelector(
            '#media-library-content .grid'
          );
          if (mediaGrid) {
            data.files.forEach((media) => {
              const mediaElement = createModalMediaElement(media);
              mediaGrid.insertBefore(mediaElement, mediaGrid.firstChild);
            });

            // Re-attach click handlers to all media items
            makeMediaItemsSelectable();
          }

          resetModalUploadForm();
          uploadBox.classList.add('hidden');
          showModalNotification(data.message, 'success');
        } else {
          showModalNotification('Upload failed', 'error');
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        showModalNotification('Upload failed', 'error');
      })
      .finally(() => {
        uploadProgress.classList.add('hidden');
        uploadSubmitBtn.disabled = false;
        uploadSubmitBtn.textContent = 'Upload Files';
      });
  });

  // Drag and drop for modal
  const dropZone = uploadBox?.querySelector('.border-dashed');
  if (dropZone) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
      dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach((eventName) => {
      dropZone.addEventListener(
        eventName,
        () => {
          dropZone.classList.add('border-blue-400', 'bg-blue-50');
        },
        false
      );
    });

    ['dragleave', 'drop'].forEach((eventName) => {
      dropZone.addEventListener(
        eventName,
        () => {
          dropZone.classList.remove('border-blue-400', 'bg-blue-50');
        },
        false
      );
    });

    dropZone.addEventListener(
      'drop',
      function (e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;

        const hasFiles = files.length > 0;
        uploadSubmitBtn.disabled = !hasFiles;

        if (hasFiles) {
          uploadSubmitBtn.textContent = `Upload ${files.length} file(s)`;
        }
      },
      false
    );
  }
}

function resetModalUploadForm() {
  const uploadForm = document.getElementById('modal-upload-form');
  const uploadSubmitBtn = document.getElementById('modal-upload-submit');
  const uploadProgress = document.getElementById('modal-upload-progress');
  const progressBar = document.getElementById('modal-progress-bar');

  uploadForm.reset();
  uploadSubmitBtn.disabled = true;
  uploadSubmitBtn.textContent = 'Upload Files';
  uploadProgress.classList.add('hidden');
  progressBar.style.width = '0%';
}

function createModalMediaElement(media) {
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
        <div class="aspect-square relative overflow-hidden bg-gray-100">
            ${preview}
        </div>
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

function showModalNotification(message, type = 'info') {
  const notification = document.createElement('div');
  const bgColor =
    type === 'success'
      ? 'bg-green-100 border-green-500 text-green-800'
      : type === 'error'
      ? 'bg-red-100 border-red-500 text-red-800'
      : 'bg-blue-100 border-blue-500 text-blue-800';

  notification.className = `absolute top-4 right-4 max-w-sm p-3 rounded-lg shadow-lg border-l-4 ${bgColor} z-10`;
  notification.innerHTML = `
        <div class="flex items-center">
            <span class="text-sm font-medium">${message}</span>
            <button class="ml-3 text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

  document.getElementById('media-library-modal').appendChild(notification);

  // Auto remove after 3 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 3000);
}

function closeMediaLibrary() {
  const modal = document.getElementById('media-library-modal');
  if (modal) {
    modal.remove();
    document.body.style.overflow = '';
  }
  selectedMediaItem = null;
  window.mediaLibraryContext = null;
}

function insertSelectedMedia() {
  if (!selectedMediaItem) return;

  if (window.mediaLibraryContext === 'featured-image') {
    setFeaturedImage();
  } else {
    insertMediaIntoCKEditor();
  }
}

function setFeaturedImage() {
  // Get media details first
  fetch(`/dashboard/media/${selectedMediaItem.id}/`, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
    .then((response) => response.json())
    .then((data) => {
      // Only allow images for featured image
      if (data.type !== 'image') {
        alert('Please select an image file for the featured image.');
        return;
      }

      // Update the featured image preview and name display
      const preview = document.getElementById('featured-image-preview');
      const img = preview.querySelector('img');
      const nameDisplay = document.getElementById('featured-image-name'); // Updated ID

      img.src = data.url;
      preview.classList.remove('hidden');
      nameDisplay.textContent = data.name; // Updated to use new element

      // Store the media ID for form submission
      const hiddenInput =
        document.getElementById('selected-featured-image-id') ||
        createHiddenFeaturedImageInput();
      hiddenInput.value = data.id;

      closeMediaLibrary();
      postEditor.scheduleAutoSave(); // Auto-save the change
    })
    .catch((error) => {
      console.error('Error setting featured image:', error);
      alert('Error setting featured image. Please try again.');
    });
}

function handleFeaturedImageSelection(imageData) {
  const preview = document.getElementById('featured-image-preview');
  const nameDisplay = document.getElementById('featured-image-name');
  const hiddenInput = document.getElementById('selected-featured-image-id');
  const img = preview.querySelector('img');

  // Update hidden input with image ID
  hiddenInput.value = imageData.id;

  // Update display name
  nameDisplay.textContent = imageData.name || 'Selected image';

  // Update preview image
  img.src = imageData.url;
  preview.classList.remove('hidden');

  // Trigger autosave
  postEditor.scheduleAutoSave();
}

function createHiddenFeaturedImageInput() {
  const input = document.createElement('input');
  input.type = 'hidden';
  input.id = 'selected-featured-image-id';
  input.name = 'selected_featured_image_id';
  document.querySelector('form').appendChild(input);
  return input;
}

function insertMediaIntoCKEditor() {
  if (!selectedMediaItem) return;

  // Get media details first
  fetch(`/dashboard/media/${selectedMediaItem.id}/`, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const mediaHtml = createMediaHtml(data);
      insertHtmlIntoCKEditor(mediaHtml);
      closeMediaLibrary();
    })
    .catch((error) => {
      console.error('Error getting media details:', error);
      // Fallback to basic insertion
      const mediaHtml = `<img src="${selectedMediaItem.url}" alt="${selectedMediaItem.alt}" style="max-width: 100%; height: auto;">`;
      insertHtmlIntoCKEditor(mediaHtml);
      closeMediaLibrary();
    });
}

function createMediaHtml(mediaData) {
  if (mediaData.type === 'image') {
    return `<img src="${mediaData.url}" alt="${
      mediaData.alt_text || ''
    }" style="max-width: 100%; height: auto;">`;
  } else if (mediaData.type === 'video') {
    return `<video controls style="max-width: 100%; height: auto;">
                    <source src="${mediaData.url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>`;
  } else if (mediaData.type === 'audio') {
    return `<audio controls style="width: 100%;">
                    <source src="${mediaData.url}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>`;
  } else {
    // For documents and other files, create a download link
    return `<a href="${mediaData.url}" target="_blank" style="display: inline-block; padding: 8px 12px; background-color: #f3f4f6; border: 1px solid #d1d5db; border-radius: 4px; text-decoration: none; color: #374151;">
                    <i class="fas fa-file" style="margin-right: 8px;"></i>
                    ${mediaData.name}
                </a>`;
  }
}

function insertHtmlIntoCKEditor(html) {
  // Try to get the CKEditor instance and insert at cursor position
  if (window.CKEDITOR && window.CKEDITOR.instances) {
    // Classic CKEditor
    for (let instanceName in window.CKEDITOR.instances) {
      const editor = window.CKEDITOR.instances[instanceName];
      editor.insertHtml(html);
      break;
    }
  } else {
    // CKEditor 5 - more complex approach
    const editorElement = document.querySelector('.ck-editor__editable');
    if (editorElement) {
      // Get the CKEditor 5 instance
      const editorInstance = editorElement.ckeditorInstance;
      if (editorInstance) {
        editorInstance.model.change((writer) => {
          const viewFragment = editorInstance.data.processor.toView(html);
          const modelFragment = editorInstance.data.toModel(viewFragment);
          editorInstance.model.insertContent(modelFragment);
        });
      }
    }
  }
}

// Initialize when DOM is ready
let postEditor;
document.addEventListener('DOMContentLoaded', function () {
  postEditor = new PostEditor();
});
