/**
 * Markdown Renderer Utility
 * Converts a subset of markdown syntax to React elements
 * Supports: headings (##, ###), bold text (**text**), and bullet lists (-, *, 1.)
 * 
 * @param {string} text - Markdown text to render
 * @returns {React.Element|null} Rendered React element or null if text is empty
 */

import React from 'react';

export function renderMarkdown(text) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let currentParagraph = [];
  let currentListItems = [];
  let key = 0;

  const processParagraph = () => {
    if (currentParagraph.length === 0) return;
    
    const paragraphText = currentParagraph.join(' ');
    const processed = processBold(paragraphText);
    elements.push(
      <p key={key++} className="mb-4 leading-relaxed">
        {processed}
      </p>
    );
    currentParagraph = [];
  };

  const processList = () => {
    if (currentListItems.length === 0) return;
    
    const listElements = currentListItems.map((item, idx) => (
      <li key={`li-${key++}-${idx}`} className="mb-2">
        <span>{processBold(item)}</span>
      </li>
    ));
    
    elements.push(
      <ul key={`ul-${key++}`} className="mb-4 ml-6 list-disc space-y-2">
        {listElements}
      </ul>
    );
    currentListItems = [];
  };

  const processBold = (text) => {
    const parts = [];
    const boldRegex = /\*\*(.+?)\*\*/g;
    let lastIndex = 0;
    let match;
    let boldKey = 0;

    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before bold
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      // Add bold text
      parts.push(
        <strong key={`bold-${key++}-${boldKey++}`} className="font-bold text-violet-300">
          {match[1]}
        </strong>
      );
      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  lines.forEach((line) => {
    const trimmed = line.trim();

    // Empty line - process current paragraph and list
    if (trimmed === '') {
      processParagraph();
      processList();
      return;
    }

    // Heading (## Heading)
    if (trimmed.startsWith('## ')) {
      processParagraph();
      processList();
      const headingText = trimmed.substring(3).trim();
      elements.push(
        <h2 key={key++} className="text-2xl font-bold text-violet-400 mt-6 mb-4 first:mt-0">
          {processBold(headingText)}
        </h2>
      );
      return;
    }

    // Heading (### Heading)
    if (trimmed.startsWith('### ')) {
      processParagraph();
      processList();
      const headingText = trimmed.substring(4).trim();
      elements.push(
        <h3 key={key++} className="text-xl font-bold text-violet-300 mt-5 mb-3">
          {processBold(headingText)}
        </h3>
      );
      return;
    }

    // Bullet point (- or * or 1.)
    if (trimmed.match(/^[-*]\s+/) || trimmed.match(/^\d+\.\s+/)) {
      processParagraph();
      const bulletText = trimmed.replace(/^[-*]\s+/, '').replace(/^\d+\.\s+/, '').trim();
      currentListItems.push(bulletText);
      return;
    }

    // Regular text - add to current paragraph
    processList();
    currentParagraph.push(trimmed);
  });

  // Process any remaining paragraph and list
  processParagraph();
  processList();

  return <div className="markdown-content">{elements}</div>;
}
