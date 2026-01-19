/**
 * Results Widget
 * 
 * Displays body composition analysis results.
 */

import React from 'react';
import { useHostState, useTheme } from '../shared/hooks.js';

export default function Results() {
  const { toolOutput } = useHostState();
  const { colors } = useTheme();

  if (!toolOutput?.structuredContent) {
    return (
      <div style={{
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        padding: '24px',
        textAlign: 'center',
        color: colors.textSecondary,
      }}>
        <p>No analysis results available.</p>
      </div>
    );
  }

  const {
    body_fat_percentage,
    confidence,
    photo_quality,
    reasoning,
    created_at,
    faces_anonymized,
  } = toolOutput.structuredContent;

  // Get confidence color and emoji
  const confidenceConfig = {
    high: { color: colors.success, emoji: '🟢', label: 'High Confidence' },
    medium: { color: colors.warning, emoji: '🟡', label: 'Medium Confidence' },
    low: { color: colors.error, emoji: '🔴', label: 'Low Confidence' },
  };
  const confConfig = confidenceConfig[confidence] || confidenceConfig.medium;

  // Get quality stars
  const qualityStars = {
    excellent: '⭐⭐⭐',
    good: '⭐⭐',
    fair: '⭐',
    poor: '❌',
  }[photo_quality] || '⭐';

  // Format date
  const analysisDate = new Date(created_at).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '24px',
      maxWidth: '600px',
      margin: '0 auto',
      backgroundColor: colors.background,
      color: colors.text,
    }}>
      {/* Header */}
      <div style={{
        textAlign: 'center',
        marginBottom: '32px',
      }}>
        <div style={{ fontSize: '48px', marginBottom: '8px' }}>✅</div>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '28px' }}>
          Analysis Complete!
        </h2>
        <p style={{ color: colors.textSecondary, margin: 0, fontSize: '14px' }}>
          {analysisDate}
        </p>
      </div>

      {/* Main Result */}
      <div style={{
        backgroundColor: `${colors.primary}22`,
        border: `2px solid ${colors.primary}`,
        borderRadius: '16px',
        padding: '24px',
        textAlign: 'center',
        marginBottom: '24px',
      }}>
        <p style={{
          fontSize: '14px',
          textTransform: 'uppercase',
          fontWeight: 600,
          letterSpacing: '1px',
          color: colors.primary,
          margin: '0 0 8px 0',
        }}>
          Body Fat Percentage
        </p>
        <div style={{
          fontSize: '56px',
          fontWeight: 700,
          color: colors.primary,
          margin: '8px 0',
        }}>
          {body_fat_percentage}%
        </div>
      </div>

      {/* Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '16px',
        marginBottom: '24px',
      }}>
        {/* Confidence */}
        <div style={{
          backgroundColor: colors.surface,
          borderRadius: '12px',
          padding: '16px',
          border: `1px solid ${colors.border}`,
        }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>
            {confConfig.emoji}
          </div>
          <p style={{
            fontSize: '12px',
            textTransform: 'uppercase',
            color: colors.textSecondary,
            margin: '0 0 4px 0',
          }}>
            Confidence
          </p>
          <p style={{
            fontSize: '16px',
            fontWeight: 600,
            color: confConfig.color,
            margin: 0,
          }}>
            {confConfig.label}
          </p>
        </div>

        {/* Photo Quality */}
        <div style={{
          backgroundColor: colors.surface,
          borderRadius: '12px',
          padding: '16px',
          border: `1px solid ${colors.border}`,
        }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>
            {qualityStars}
          </div>
          <p style={{
            fontSize: '12px',
            textTransform: 'uppercase',
            color: colors.textSecondary,
            margin: '0 0 4px 0',
          }}>
            Photo Quality
          </p>
          <p style={{
            fontSize: '16px',
            fontWeight: 600,
            margin: 0,
            textTransform: 'capitalize',
          }}>
            {photo_quality}
          </p>
        </div>
      </div>

      {/* Analysis Reasoning */}
      <div style={{
        backgroundColor: colors.surface,
        borderRadius: '12px',
        padding: '20px',
        border: `1px solid ${colors.border}`,
        marginBottom: '24px',
      }}>
        <p style={{
          fontSize: '14px',
          fontWeight: 600,
          margin: '0 0 12px 0',
        }}>
          💡 Analysis Details
        </p>
        <p style={{
          fontSize: '14px',
          lineHeight: '1.6',
          color: colors.textSecondary,
          margin: 0,
        }}>
          {reasoning}
        </p>
      </div>

      {/* Privacy Notice */}
      {faces_anonymized && (
        <div style={{
          backgroundColor: `${colors.success}11`,
          border: `1px solid ${colors.success}`,
          borderRadius: '8px',
          padding: '12px 16px',
          marginBottom: '16px',
        }}>
          <p style={{
            fontSize: '13px',
            color: colors.success,
            margin: 0,
          }}>
            🔒 Privacy Protected: Your face was automatically blurred
          </p>
        </div>
      )}

      {/* Disclaimer */}
      <div style={{
        backgroundColor: colors.surface,
        borderRadius: '8px',
        padding: '12px 16px',
        border: `1px solid ${colors.border}`,
      }}>
        <p style={{
          fontSize: '12px',
          color: colors.textSecondary,
          margin: 0,
          lineHeight: '1.5',
        }}>
          ⚠️ <strong>Important:</strong> This is an AI estimate for informational purposes only, not medical advice. 
          Consult healthcare professionals for accurate body composition measurements.
        </p>
      </div>

      {/* Action */}
      <div style={{
        marginTop: '24px',
        textAlign: 'center',
      }}>
        <p style={{
          fontSize: '13px',
          color: colors.textSecondary,
          margin: '0 0 8px 0',
        }}>
          Want to track your progress over time?
        </p>
        <p style={{
          fontSize: '13px',
          color: colors.primary,
          margin: 0,
          fontWeight: 500,
        }}>
          Run another analysis in a few weeks to see your changes!
        </p>
      </div>
    </div>
  );
}
