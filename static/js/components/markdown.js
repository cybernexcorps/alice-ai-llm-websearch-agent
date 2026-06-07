/**
 * markdown.js — marked.js wrapper with DOMPurify sanitization
 */

const Markdown = (() => {
  // Configure marked for safe output
  if (typeof marked !== 'undefined') {
    marked.use({
      gfm: true,
      breaks: true,
    });
  }

  function render(text) {
    if (!text) return '';
    if (typeof marked === 'undefined') {
      // Fallback: escape HTML and preserve line breaks
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>');
    }
    const html = marked.parse(text);
    if (typeof DOMPurify !== 'undefined') {
      return DOMPurify.sanitize(html, {
        ALLOWED_TAGS: [
          'p','br','strong','em','b','i','s','del','ins',
          'h1','h2','h3','h4','h5','h6',
          'ul','ol','li','blockquote',
          'code','pre','a','table','thead','tbody','tr','th','td',
          'hr','img','span','div',
        ],
        ALLOWED_ATTR: ['href','target','rel','src','alt','class'],
      });
    }
    return html;
  }

  return { render };
})();

window.Markdown = Markdown;
