// Initialize Mermaid with configuration
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'strict',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
});

// DOM Elements
const editor = document.getElementById('editor');
const preview = document.getElementById('preview');
const errorDiv = document.getElementById('error');
const status = document.getElementById('status');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const clearBtn = document.getElementById('clearBtn');
const resizer = document.getElementById('resizer');

// Debounce utility
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Render diagram
let renderCount = 0;

async function renderDiagram() {
  const code = editor.value.trim();

  if (!code) {
    preview.innerHTML = '<div style="color: #999; font-size: 14px;">Enter Mermaid code on the left to see the preview</div>';
    errorDiv.classList.remove('visible');
    status.textContent = 'Ready';
    status.className = 'hint';
    return;
  }

  try {
    // Validate the syntax first
    await mermaid.parse(code);

    // Generate unique ID for each render
    renderCount++;
    const id = `mermaid-diagram-${renderCount}`;

    // Render the diagram
    const { svg } = await mermaid.render(id, code);

    preview.innerHTML = svg;
    errorDiv.classList.remove('visible');
    status.textContent = 'Rendered';
    status.className = 'hint success';
  } catch (err) {
    errorDiv.textContent = err.message || 'Invalid Mermaid syntax';
    errorDiv.classList.add('visible');
    status.textContent = 'Error';
    status.className = 'hint error';
  }
}

// Debounced render for real-time updates
const debouncedRender = debounce(renderDiagram, 300);

// Event listeners
editor.addEventListener('input', debouncedRender);

// Copy button
copyBtn.addEventListener('click', async () => {
  const code = editor.value.trim();
  if (!code) return;

  try {
    await navigator.clipboard.writeText(code);
    showFeedback('Code copied to clipboard!');
  } catch (err) {
    showFeedback('Failed to copy', true);
  }
});

// Download SVG button
downloadBtn.addEventListener('click', () => {
  const svg = preview.querySelector('svg');
  if (!svg) {
    showFeedback('No diagram to download', true);
    return;
  }

  const svgData = new XMLSerializer().serializeToString(svg);
  const blob = new Blob([svgData], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = 'mermaid-diagram.svg';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  showFeedback('SVG downloaded!');
});

// Clear button
clearBtn.addEventListener('click', () => {
  editor.value = '';
  renderDiagram();
});

// Show feedback message
function showFeedback(message, isError = false) {
  const feedback = document.createElement('div');
  feedback.className = 'copy-feedback';
  feedback.textContent = message;
  if (isError) {
    feedback.style.background = '#ef4444';
  }
  document.body.appendChild(feedback);

  setTimeout(() => {
    feedback.remove();
  }, 2000);
}

// Resizer functionality
let isResizing = false;

resizer.addEventListener('mousedown', (e) => {
  isResizing = true;
  resizer.classList.add('active');
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';
});

document.addEventListener('mousemove', (e) => {
  if (!isResizing) return;

  const container = document.querySelector('.main');
  const containerRect = container.getBoundingClientRect();
  const editorPane = document.querySelector('.editor-pane');
  const previewPane = document.querySelector('.preview-pane');

  const newEditorWidth = e.clientX - containerRect.left;
  const containerWidth = containerRect.width;

  // Ensure minimum widths
  if (newEditorWidth < 300 || (containerWidth - newEditorWidth - 6) < 300) return;

  const editorPercent = (newEditorWidth / containerWidth) * 100;
  const previewPercent = 100 - editorPercent;

  editorPane.style.flex = `0 0 ${editorPercent}%`;
  previewPane.style.flex = `0 0 ${previewPercent}%`;
});

document.addEventListener('mouseup', () => {
  if (isResizing) {
    isResizing = false;
    resizer.classList.remove('active');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }
});

// Load saved content from localStorage
const savedContent = localStorage.getItem('mermaid-editor-content');
if (savedContent) {
  editor.value = savedContent;
  renderDiagram();
} else {
  // Set default example
  editor.value = `graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
    C --> E[Deploy]`;
  renderDiagram();
}

// Auto-save content
editor.addEventListener('input', debounce(() => {
  localStorage.setItem('mermaid-editor-content', editor.value);
}, 1000));

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Ctrl/Cmd + S to save (prevent default and show feedback)
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    localStorage.setItem('mermaid-editor-content', editor.value);
    showFeedback('Content saved!');
  }

  // Ctrl/Cmd + Shift + C to copy code
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
    e.preventDefault();
    copyBtn.click();
  }
});
