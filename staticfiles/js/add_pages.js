class PageEditor {
  constructor() {
    this.pageId = window.djangoData ? window.djangoData.pageId : null;
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
    // Title input for permalink generation and auto-save
    const titleInput = document.getElementById('id_title');
    if (titleInput) {
      titleInput.addEventListener('input', (e) => {
        this.handleTitleChange();
      });
      titleInput.addEventListener('blur', () => {
        this.scheduleAutoSave();
      });
    }

    // Auto-save for all other inputs
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
        field.addEventListener('change', () => this.scheduleAutoSave());
      }
    });

    // SEO character counter
    const seoInput = document.getElementById('id_seo_description');
    if (seoInput) {
      seoInput.addEventListener('input', this.updateCharCounter.bind(this));
    }

    // CKEditor content change detection
    this.bindCKEditorEvents();
  }

  bindCKEditorEvents() {
    const checkForEditor = setInterval(() => {
      // Check for CKEditor 5
      if (window.ClassicEditor) {
        const editorElement = document.querySelector('.ck-editor__editable');
        if (editorElement) {
          const observer = new MutationObserver(() => {
            this.scheduleAutoSave();
          });
          observer.observe(editorElement, {
            childList: true,
            subtree: true,
            characterData: true,
          });
          clearInterval(checkForEditor);
          return;
        }
      }

      // Check for CKEditor 4
      if (window.CKEDITOR && window.CKEDITOR.instances) {
        for (let instanceName in window.CKEDITOR.instances) {
          const editor = window.CKEDITOR.instances[instanceName];
          editor.on('change', () => this.scheduleAutoSave());
        }
        clearInterval(checkForEditor);
        return;
      }
    }, 1000);

    // Stop checking after 10 seconds
    setTimeout(() => clearInterval(checkForEditor), 10000);
  }

  handleTitleChange() {
    const titleInput = document.getElementById('id_title');
    const permalinkSection = document.getElementById('permalink-section');

    if (titleInput.value.trim()) {
      permalinkSection?.classList.remove('hidden');

      if (!this.isSlugManuallyEdited()) {
        clearTimeout(this.slugTimeout);
        this.slugTimeout = setTimeout(() => this.generateSlug(), 500);
      }
    } else {
      // Only hide if there's no existing slug
      const slugInput = document.getElementById('id_slug');
      if (!slugInput?.value) {
        permalinkSection?.classList.add('hidden');
      }
    }

    this.scheduleAutoSave();
  }

  isSlugManuallyEdited() {
    const slugInput = document.getElementById('id_slug');
    const titleInput = document.getElementById('id_title');
    if (!slugInput || !titleInput) return false;

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
    const slugInput = document.getElementById('id_slug');

    if (!titleInput || !slugInput) return;

    const title = titleInput.value.trim();
    if (!title) return;

    const url = window.djangoData.urls.generateSlug;
    const queryString = `?title=${encodeURIComponent(title)}&page_id=${
      this.pageId || ''
    }`;

    fetch(`${url}${queryString}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.slug) {
          slugInput.value = data.slug;
          this.updateSlugDisplay(data.slug);

          // Show permalink section when slug is generated
          const permalinkSection = document.getElementById('permalink-section');
          if (permalinkSection) {
            permalinkSection.classList.remove('hidden');
          }
        }
      })
      .catch((error) => {
        console.error('Error generating slug:', error);
        // Fallback to client-side slug generation
        const fallbackSlug = this.slugify(title);
        slugInput.value = fallbackSlug;
        this.updateSlugDisplay(fallbackSlug);

        const permalinkSection = document.getElementById('permalink-section');
        if (permalinkSection) {
          permalinkSection.classList.remove('hidden');
        }
      });
  }

  updateSlugDisplay(slug) {
    const slugDisplay = document.getElementById('slug-display');
    if (slugDisplay) {
      slugDisplay.textContent = slug;
    }
  }

  initPermalink() {
    const slugInput = document.getElementById('id_slug');
    const slugDisplay = document.getElementById('slug-display');
    const permalinkSection = document.getElementById('permalink-section');

    if (slugInput) {
      this.originalSlug = slugInput.value;
      if (slugDisplay) {
        slugDisplay.textContent = slugInput.value || '';
      }
      // Always show permalink section, hide only if completely empty
      const titleInput = document.getElementById('id_title');
      if (!slugInput.value && !titleInput?.value) {
        permalinkSection?.classList.add('hidden');
      }
    }
  }

  updateCharCounter() {
    const seoInput = document.getElementById('id_seo_description');
    const counter = document.getElementById('seo-char-count');
    const warning = document.getElementById('seo-char-warning');

    if (seoInput && counter) {
      const currentLength = seoInput.value.length;
      const maxLength = 160;
      counter.textContent = currentLength;

      if (warning) {
        if (currentLength > maxLength) {
          warning.classList.remove('hidden');
          counter.classList.add('text-red-500');
          counter.classList.remove('text-gray-500');
        } else {
          warning.classList.add('hidden');
          counter.classList.remove('text-red-500');
          counter.classList.add('text-gray-500');
        }
      }
    }
  }

  initCharCounter() {
    const seoInput = document.getElementById('id_seo_description');
    if (seoInput) {
      this.updateCharCounter();
    }
  }

  scheduleAutoSave() {
    clearTimeout(this.autoSaveTimeout);
    this.showAutoSaveIndicator(true);

    this.autoSaveTimeout = setTimeout(() => {
      this.autoSave();
    }, 2000);
  }

  hasContent() {
    const titleInput = document.getElementById('id_title');
    const contentInput = this.getCKEditorContent();

    return (
      (titleInput && titleInput.value.trim()) ||
      (contentInput && contentInput.trim())
    );
  }

  autoSave() {
    const formData = this.collectFormData();
    const url = window.djangoData.urls.autoSavePage;

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCSRFToken(),
      },
      body: JSON.stringify(formData),
    })
      .then((response) => response.json())
      .then((data) => {
        this.showAutoSaveIndicator(false);

        if (data.success) {
          this.showSaveSuccess(data.message);

          // Update page ID if it's a new page
          if (data.page_id && !this.pageId) {
            this.pageId = data.page_id;
            // Update djangoData for future requests
            if (window.djangoData) {
              window.djangoData.pageId = data.page_id;
            }
            // Update form action and URL for new pages
            const form = document.getElementById('page-form');
            if (form && !form.action.includes('/edit-page/')) {
              const newUrl = `${window.djangoData.urls.editPageUrl}${data.page_id}/`;
              window.history.replaceState({}, '', newUrl);
            }
          }

          // Update slug if generated
          if (data.slug) {
            const slugInput = document.getElementById('id_slug');
            const slugDisplay = document.getElementById('slug-display');

            // Always update slug input with server response
            if (slugInput) {
              slugInput.value = data.slug;
            }

            // Update display
            if (slugDisplay) {
              slugDisplay.textContent = data.slug;
            }

            // Show permalink section
            const permalinkSection =
              document.getElementById('permalink-section');
            if (permalinkSection) {
              permalinkSection.classList.remove('hidden');
            }
          }
        } else {
          this.showSaveError(data.message || 'Auto-save failed');
        }
      })
      .catch((error) => {
        this.showAutoSaveIndicator(false);
        console.error('Auto-save error:', error);
        this.showSaveError('Auto-save failed');
      });
  }

  collectFormData() {
    const title = document.getElementById('id_title')?.value?.trim() || '';
    const slug = document.getElementById('id_slug')?.value?.trim() || '';

    return {
      page_id: this.pageId,
      title: title,
      slug: slug, // FIX: Don't auto-generate slug here, let backend handle it
      content: this.getCKEditorContent(),
      excerpt: document.getElementById('id_excerpt')?.value || '',
      seo_description:
        document.getElementById('id_seo_description')?.value || '',
      seo_keywords: document.getElementById('id_seo_keywords')?.value || '',
      featured_image_id:
        document.getElementById('selected-featured-image-id')?.value || '',
    };
  }

  getCKEditorContent() {
    // Try CKEditor 5 first
    if (window.ClassicEditor) {
      const editorElement = document.querySelector('.ck-editor__editable');
      if (editorElement) {
        return editorElement.innerHTML;
      }
    }

    // Try CKEditor 4
    if (window.CKEDITOR && window.CKEDITOR.instances) {
      for (let instanceName in window.CKEDITOR.instances) {
        const editor = window.CKEDITOR.instances[instanceName];
        if (editor && editor.getData) {
          return editor.getData();
        }
      }
    }

    // Fallback to textarea
    const contentTextarea = document.getElementById('id_content');
    return contentTextarea ? contentTextarea.value : '';
  }

  getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : window.djangoData?.csrfToken || '';
  }

  showAutoSaveIndicator(show) {
    const indicator = document.getElementById('autosave-indicator');
    if (indicator) {
      if (show) {
        indicator.classList.remove('hidden');
      } else {
        indicator.classList.add('hidden');
      }
    }
  }

  showSaveSuccess(message) {
    this.showMessage(message, 'success');
  }

  showSaveError(message) {
    this.showMessage(message, 'error');
  }

  showMessage(message, type) {
    // Use the same autosave indicator element
    const indicator = document.getElementById('autosave-indicator');
    if (indicator) {
      // Clear any existing timeout
      clearTimeout(this.messageTimeout);

      // Update styling based on message type
      if (type === 'success') {
        indicator.className =
          'fixed bottom-4 right-4 bg-green-100 text-green-800 px-4 py-2 rounded-md shadow-lg z-50';
      } else {
        indicator.className =
          'fixed bottom-4 right-4 bg-red-100 text-red-800 px-4 py-2 rounded-md shadow-lg z-50';
      }

      // Update content
      indicator.innerHTML = `
      <div class="flex items-center text-sm">
        <span>${message}</span>
      </div>
    `;

      // Show the message
      indicator.classList.remove('hidden');

      // Auto-hide after delay
      this.messageTimeout = setTimeout(
        () => {
          indicator.classList.add('hidden');
        },
        type === 'success' ? 3000 : 5000
      );
    }
  }
}



// Global functions for permalink editing
function editPermalink() {
  const slugDisplay = document.getElementById('slug-display');
  const slugEdit = document.getElementById('slug-edit');
  const editBtn = document.getElementById('edit-slug-btn');
  const saveBtn = document.getElementById('save-slug-btn');
  const cancelBtn = document.getElementById('cancel-slug-btn');

  if (slugDisplay && slugEdit) {
    slugDisplay.classList.add('hidden');
    slugEdit.classList.remove('hidden');
    editBtn?.classList.add('hidden');
    saveBtn?.classList.remove('hidden');
    cancelBtn?.classList.remove('hidden');

    const slugInput = document.getElementById('id_slug');
    if (slugInput && window.pageEditor) {
      slugInput.focus();
      window.pageEditor.originalSlug = slugInput.value;
    }
  }
}

function savePermalink() {
  const slugDisplay = document.getElementById('slug-display');
  const slugEdit = document.getElementById('slug-edit');
  const slugInput = document.getElementById('id_slug');
  const editBtn = document.getElementById('edit-slug-btn');
  const saveBtn = document.getElementById('save-slug-btn');
  const cancelBtn = document.getElementById('cancel-slug-btn');

  if (slugDisplay && slugEdit && slugInput) {
    // Validate slug is not empty
    const newSlug = slugInput.value.trim();
    if (!newSlug) {
      alert('Slug cannot be empty');
      return;
    }

    // Update display
    slugDisplay.textContent = newSlug;

    // Toggle visibility
    slugDisplay.classList.remove('hidden');
    slugEdit.classList.add('hidden');
    editBtn?.classList.remove('hidden');
    saveBtn?.classList.add('hidden');
    cancelBtn?.classList.add('hidden');

    // Update original slug and trigger auto-save
    if (window.pageEditor) {
      window.pageEditor.originalSlug = newSlug;
      window.pageEditor.scheduleAutoSave();
    }
  }
}

function cancelEditPermalink() {
  const slugDisplay = document.getElementById('slug-display');
  const slugEdit = document.getElementById('slug-edit');
  const slugInput = document.getElementById('id_slug');
  const editBtn = document.getElementById('edit-slug-btn');
  const saveBtn = document.getElementById('save-slug-btn');
  const cancelBtn = document.getElementById('cancel-slug-btn');

  if (slugDisplay && slugEdit && slugInput && window.pageEditor) {
    // Restore original slug
    const originalSlug = window.pageEditor.originalSlug || '';
    slugInput.value = originalSlug;
    slugDisplay.textContent = originalSlug;

    // Toggle visibility
    slugDisplay.classList.remove('hidden');
    slugEdit.classList.add('hidden');
    editBtn?.classList.remove('hidden');
    saveBtn?.classList.add('hidden');
    cancelBtn?.classList.add('hidden');
  }
}

// Featured image functions
function removeFeaturedImage() {
  const pageId = window.djangoData?.pageId;
  if (!pageId) {
    alert('Please save the page first before removing the featured image.');
    return;
  }

  if (!confirm('Are you sure you want to remove the featured image?')) {
    return;
  }

  const url =
    window.djangoData?.removeFeaturedImageUrl ||
    '/dashboard/remove-page-featured-image/';

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken':
        document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
    },
    body: JSON.stringify({ page_id: pageId }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const featuredImagePreview = document.getElementById(
          'featured-image-preview'
        );
        const featuredImageInput = document.getElementById(
          'selected-featured-image-id'
        );
        const featuredImageName = document.getElementById(
          'featured-image-name'
        );

        if (featuredImagePreview) {
          featuredImagePreview.classList.add('hidden');
        }
        if (featuredImageInput) {
          featuredImageInput.value = '';
        }
        if (featuredImageName) {
          featuredImageName.textContent = 'No image selected';
        }

        if (window.pageEditor) {
          window.pageEditor.scheduleAutoSave();
        }
      } else {
        alert('Error removing featured image: ' + data.error);
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      alert('Error removing featured image');
    });
}

function previewPage() {
  const pageId = window.djangoData?.pageId;
  if (pageId) {
    window.open(`/dashboard/page-preview/${pageId}/`, '_blank');
  } else {
    alert('Please save the page first before previewing.');
  }
}

// Media library functions
// Media library functions - REPLACE ENTIRE SECTION
function openMediaLibrary(context = 'editor') {
  window.mediaLibraryContext = context;
  createMediaLibraryModal();
}

function createMediaLibraryModal() {
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
                document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                ''
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
              <span id="media-library-instruction">Select an image to insert into your page</span>
            </div>
            <button id="insert-selected-media" disabled class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed">
              <span id="insert-button-text">Insert Selected</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHTML);
  document.body.style.overflow = 'hidden';

  loadMediaLibraryContent();
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
                <p class="text-xs text-gray-500 mt-0.5">${media.size}</p>
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
        instruction.textContent = 'Select an image to insert into your page';
        buttonText.textContent = 'Insert Selected';
      }

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
  const mediaItems = document.querySelectorAll('#media-library-modal .media-item');
  const insertButton = document.getElementById('insert-selected-media');

  mediaItems.forEach((item) => {
    item.addEventListener('click', function () {
      if (window.mediaLibraryContext === 'featured-image') {
        const img = this.querySelector('img');
        if (!img) {
          alert('Please select an image file for the featured image.');
          return;
        }
      }

      mediaItems.forEach((i) => i.classList.remove('ring-4', 'ring-blue-500'));
      this.classList.add('ring-4', 'ring-blue-500');

      selectedMediaItem = {
        id: this.dataset.mediaId,
        url: this.querySelector('img')?.src || '',
        alt: this.querySelector('img')?.alt || '',
        name: this.querySelector('p')?.textContent || '',
      };

      insertButton.disabled = false;
    });
  });
}

function bindMediaLibraryEvents() {
  document
    .getElementById('close-media-library')
    .addEventListener('click', closeMediaLibrary);
  document
    .getElementById('insert-selected-media')
    .addEventListener('click', insertSelectedMedia);
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

    const csrfToken = document.querySelector(
      '[name=csrfmiddlewaretoken]'
    )?.value;
    if (csrfToken) {
      formData.append('csrfmiddlewaretoken', csrfToken);
    }

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
          const mediaGrid = document.querySelector(
            '#media-library-content .grid'
          );
          if (mediaGrid) {
            data.files.forEach((media) => {
              const mediaElement = createModalMediaElement(media);
              mediaGrid.insertBefore(mediaElement, mediaGrid.firstChild);
            });
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

function insertSelectedMedia() {
  if (!selectedMediaItem) return;

  if (window.mediaLibraryContext === 'featured-image') {
    setFeaturedImageFromLibrary();
  } else {
    insertMediaIntoCKEditor();
  }
}

function insertMediaIntoCKEditor() {
  if (!selectedMediaItem) return;

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
    return `<a href="${mediaData.url}" target="_blank" style="display: inline-block; padding: 8px 12px; background-color: #f3f4f6; border: 1px solid #d1d5db; border-radius: 4px; text-decoration: none; color: #374151;">
              <i class="fas fa-file" style="margin-right: 8px;"></i>
              ${mediaData.name}
            </a>`;
  }
}

function insertHtmlIntoCKEditor(html) {
  if (window.CKEDITOR && window.CKEDITOR.instances) {
    for (let instanceName in window.CKEDITOR.instances) {
      const editor = window.CKEDITOR.instances[instanceName];
      editor.insertHtml(html);
      break;
    }
  } else {
    const editorElement = document.querySelector('.ck-editor__editable');
    if (editorElement) {
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

function setFeaturedImageFromLibrary() {
  fetch(`/dashboard/media/${selectedMediaItem.id}/`, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.type !== 'image') {
        alert('Please select an image file for the featured image.');
        return;
      }

      const preview = document.getElementById('featured-image-preview');
      const img = preview.querySelector('img');
      const nameDisplay = document.getElementById('featured-image-name');

      img.src = data.url;
      preview.classList.remove('hidden');
      nameDisplay.textContent = data.name;

      const hiddenInput = document.getElementById('selected-featured-image-id') || createHiddenFeaturedImageInput();
      hiddenInput.value = data.id;

      closeMediaLibrary();
      window.pageEditor.scheduleAutoSave();
    })
    .catch((error) => {
      console.error('Error setting featured image:', error);
      alert('Error setting featured image. Please try again.');
    });
}

function createHiddenFeaturedImageInput() {
  const input = document.createElement('input');
  input.type = 'hidden';
  input.id = 'selected-featured-image-id';
  input.name = 'featured_image_id';
  document.querySelector('form').appendChild(input);
  return input;
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

function closeMediaLibrary() {
  const modal = document.getElementById('media-library-modal');
  if (modal) {
    modal.remove();
    document.body.style.overflow = '';
  }
  selectedMediaItem = null;
  window.mediaLibraryContext = null;
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

  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 3000);
}

// Initialize the page editor when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  window.pageEditor = new PageEditor();
});

window.savePermalink = savePermalink;
window.cancelEditPermalink = cancelEditPermalink;