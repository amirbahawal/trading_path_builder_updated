import React, { useState } from "react";

const StageCard = ({ stage, index, isLocked, teaserBullets }) => {
  const [isExpanded, setIsExpanded] = useState(!isLocked && index === 0);
  
  // Use stage.teaser if available, otherwise fall back to teaserBullets prop
  const displayTeasers = stage?.teaser || teaserBullets || [];

  return (
    <div 
      style={{
        position: 'relative',
        marginBottom: '20px',
        borderRadius: '18px',
        border: isLocked 
          ? '1px solid rgba(255, 123, 156, 0.3)' 
          : '1px solid rgba(110, 219, 255, 0.25)',
        background: isLocked 
          ? 'rgba(10, 22, 45, 0.4)' 
          : 'rgba(10, 22, 45, 0.6)',
        overflow: 'hidden',
        filter: isLocked ? 'blur(1px)' : 'none',
        transition: 'all 0.3s ease',
        opacity: isLocked ? 0.75 : 1,
      }}
    >
      {/* Blur overlay for locked stages */}
      {isLocked && (
        <div style={{
          position: 'absolute',
          inset: 0,
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
          background: 'rgba(0, 0, 0, 0.3)',
          zIndex: 1,
          pointerEvents: 'none',
          borderRadius: '18px',
        }} />
      )}
      {/* Header */}
      <button
        onClick={() => !isLocked && setIsExpanded(!isExpanded)}
        disabled={isLocked}
        aria-expanded={isExpanded}
        aria-label={`${stage.title}${isLocked ? ' - Locked' : ''}`}
        style={{
          width: '100%',
          padding: '20px 24px',
          background: 'transparent',
          border: 'none',
          color: 'var(--text-primary)',
          textAlign: 'left',
          cursor: isLocked ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
          position: 'relative',
          zIndex: 2,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
          <span style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            background: isLocked 
              ? 'rgba(255, 123, 156, 0.2)' 
              : 'linear-gradient(135deg, rgba(124, 77, 255, 0.35), rgba(110, 219, 255, 0.25))',
            border: isLocked
              ? '1px solid rgba(255, 123, 156, 0.4)'
              : '1px solid rgba(110, 219, 255, 0.35)',
            fontSize: '1.1rem',
            fontWeight: '600',
          }}>
            {index + 1}
          </span>
          <h3 style={{ 
            margin: 0, 
            fontSize: '1.3rem', 
            fontWeight: '600',
            opacity: isLocked ? 0.85 : 1,
          }}>
            {stage.title}
          </h3>
        </div>
        
        {isLocked && (
          <span style={{
            padding: '6px 12px',
            borderRadius: '999px',
            background: 'rgba(255, 123, 156, 0.15)',
            border: '1px solid rgba(255, 123, 156, 0.3)',
            color: '#ff7b9c',
            fontSize: '0.75rem',
            fontWeight: '600',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}>
            🔒 Locked
          </span>
        )}
        
        {!isLocked && (
          <span style={{ 
            fontSize: '1.5rem',
            transition: 'transform 0.3s ease',
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
          }}>
            ▼
          </span>
        )}
      </button>

      {/* Teaser bullets when locked */}
      {isLocked && displayTeasers && displayTeasers.length > 0 && (
        <div style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(255, 123, 156, 0.08), rgba(255, 123, 156, 0.03))',
          borderTop: '1px solid rgba(255, 123, 156, 0.25)',
          position: 'relative',
          zIndex: 2,
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
        }}>
          <div style={{
            marginBottom: '12px',
            fontSize: '0.75rem',
            fontWeight: '600',
            color: '#ff7b9c',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            opacity: 0.9,
          }}>
            Preview
          </div>
          <ul style={{
            margin: 0,
            padding: '0 0 0 24px',
            color: 'var(--text-secondary)',
            fontSize: '0.95rem',
            lineHeight: '1.8',
            listStyle: 'none',
          }}>
            {displayTeasers.map((bullet, i) => (
              <li key={i} style={{ 
                marginBottom: '10px',
                position: 'relative',
                paddingLeft: '20px',
                opacity: 0.85,
              }}>
                <span style={{
                  position: 'absolute',
                  left: 0,
                  top: '8px',
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #ff7b9c, #ff9db8)',
                  boxShadow: '0 0 8px rgba(255, 123, 156, 0.5)',
                }} />
                {bullet}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Content - only show if not locked and expanded */}
      {!isLocked && isExpanded && (
        <div style={{
          padding: '0 24px 24px',
          lineHeight: '1.8',
          color: 'var(--text-secondary)',
          whiteSpace: 'pre-wrap',
        }}>
          {stage.content}
        </div>
      )}
    </div>
  );
};

export default StageCard;

