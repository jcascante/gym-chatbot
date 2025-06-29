import React from 'react';

const MarkdownRenderer = ({ content }) => {
  if (!content) return null;

  // Simple markdown parser for basic formatting
  const parseMarkdown = (text) => {
    // Split into lines
    const lines = text.split('\n');
    const elements = [];
    let currentParagraph = [];
    let inTable = false;
    let tableRows = [];

    const flushParagraph = () => {
      if (currentParagraph.length > 0) {
        const paragraphText = currentParagraph.join(' ');
        elements.push(
          <p key={`p-${elements.length}`} className="markdown-paragraph">
            {parseInlineMarkdown(paragraphText)}
          </p>
        );
        currentParagraph = [];
      }
    };

    const parseInlineMarkdown = (text) => {
      // Handle links (URLs)
      text = text.replace(
        /(https?:\/\/[^\s]+)/g, 
        '<a href="$1" target="_blank" rel="noopener noreferrer" class="markdown-link">$1</a>'
      );
      
      // Handle bold text
      text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      // Handle italic text
      text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
      // Handle line breaks
      text = text.replace(/\\n/g, '<br />');
      
      return <span dangerouslySetInnerHTML={{ __html: text }} />;
    };

    const renderTable = (rows) => {
      if (rows.length === 0) return null;

      return (
        <table key={`table-${elements.length}`} className="markdown-table">
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex}>{parseInlineMarkdown(cell)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    };

    lines.forEach((line, lineIndex) => {
      const trimmedLine = line.trim();

      // Check if this is a table row
      if (trimmedLine.startsWith('|') && trimmedLine.endsWith('|')) {
        if (!inTable) {
          flushParagraph();
          inTable = true;
          tableRows = [];
        }
        
        // Parse table row
        const cells = trimmedLine
          .slice(1, -1) // Remove leading and trailing |
          .split('|')
          .map(cell => cell.trim());
        
        // Skip separator rows (---)
        if (!cells.every(cell => cell.match(/^[-:]+$/))) {
          tableRows.push(cells);
        }
        return;
      }

      // End table if we were in one
      if (inTable) {
        elements.push(renderTable(tableRows));
        inTable = false;
        tableRows = [];
      }

      // Handle headers
      if (trimmedLine.startsWith('#')) {
        flushParagraph();
        const level = trimmedLine.match(/^#+/)[0].length;
        const headerText = trimmedLine.replace(/^#+\s*/, '');
        const HeaderTag = `h${Math.min(level, 6)}`;
        elements.push(
          React.createElement(HeaderTag, {
            key: `header-${elements.length}`,
            className: 'markdown-header'
          }, headerText)
        );
        return;
      }

      // Handle list items
      if (trimmedLine.match(/^[-*•]\s/) || trimmedLine.match(/^\d+\)\s/)) {
        flushParagraph();
        elements.push(
          <li key={`li-${elements.length}`} className="markdown-list-item">
            {parseInlineMarkdown(trimmedLine.replace(/^[-*•]\s/, '').replace(/^\d+\)\s/, ''))}
          </li>
        );
        return;
      }

      // Handle exercise items (A), B), etc.)
      if (trimmedLine.match(/^[A-Z]\)\s/)) {
        flushParagraph();
        elements.push(
          <div key={`exercise-${elements.length}`} className="markdown-exercise">
            {parseInlineMarkdown(trimmedLine)}
          </div>
        );
        return;
      }

      // Handle empty lines (paragraph breaks)
      if (trimmedLine === '') {
        flushParagraph();
        return;
      }

      // Regular text line
      currentParagraph.push(trimmedLine);
    });

    // Flush any remaining paragraph
    flushParagraph();

    // Render any remaining table
    if (inTable) {
      elements.push(renderTable(tableRows));
    }

    return elements;
  };

  return (
    <div className="markdown-content">
      {parseMarkdown(content)}
    </div>
  );
};

export default MarkdownRenderer; 