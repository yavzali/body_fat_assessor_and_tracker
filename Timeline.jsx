/**
 * Timeline Widget (Phase 3)
 * 
 * Displays body composition analysis history and progress over time.
 */

import React from 'react';
import { useHostState, useTheme } from '../shared/hooks.js';

export default function Timeline() {
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
        <p>No history data available.</p>
      </div>
    );
  }

  const { analyses, statistics } = toolOutput.structuredContent;

  if (!analyses || analyses.length === 0) {
    return (
      <div style={{
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        padding: '24px',
        textAlign: 'center',
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
        <h3 style={{ margin: '0 0 8px 0' }}>No History Yet</h3>
        <p style={{ color: colors.textSecondary, margin: 0 }}>
          Complete more analyses to track your progress over time.
        </p>
      </div>
    );
  }

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '24px',
      maxWidth: '800px',
      margin: '0 auto',
      backgroundColor: colors.background,
      color: colors.text,
    }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '28px' }}>
          📊 Your Progress
        </h2>
        <p style={{ color: colors.textSecondary, margin: 0, fontSize: '14px' }}>
          Track your body composition over time
        </p>
      </div>

      {/* Statistics Summary */}
      {statistics && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '16px',
          marginBottom: '32px',
        }}>
          <StatCard
            label="Total Analyses"
            value={statistics.total_count}
            colors={colors}
          />
          <StatCard
            label="Current"
            value={`${statistics.latest_body_fat}%`}
            colors={colors}
          />
          <StatCard
            label="Average"
            value={`${statistics.average_body_fat}%`}
            colors={colors}
          />
          <StatCard
            label="Range"
            value={`${statistics.min_body_fat}% - ${statistics.max_body_fat}%`}
            colors={colors}
          />
        </div>
      )}

      {/* Timeline */}
      <div style={{
        backgroundColor: colors.surface,
        borderRadius: '12px',
        padding: '20px',
        border: `1px solid ${colors.border}`,
      }}>
        <h3 style={{ margin: '0 0 20px 0', fontSize: '18px' }}>
          Timeline
        </h3>

        <div style={{ position: 'relative' }}>
          {/* Vertical line */}
          <div style={{
            position: 'absolute',
            left: '20px',
            top: 0,
            bottom: 0,
            width: '2px',
            backgroundColor: colors.border,
          }} />

          {/* Analysis entries */}
          {analyses.map((analysis, index) => (
            <TimelineEntry
              key={analysis.id}
              analysis={analysis}
              isLatest={index === 0}
              colors={colors}
            />
          ))}
        </div>
      </div>

      {/* Note */}
      <p style={{
        fontSize: '12px',
        color: colors.textSecondary,
        textAlign: 'center',
        marginTop: '24px',
        marginBottom: 0,
      }}>
        💡 Tip: Complete analyses regularly to see meaningful progress trends
      </p>
    </div>
  );
}

function StatCard({ label, value, colors }) {
  return (
    <div style={{
      backgroundColor: colors.surface,
      borderRadius: '12px',
      padding: '16px',
      border: `1px solid ${colors.border}`,
      textAlign: 'center',
    }}>
      <p style={{
        fontSize: '12px',
        textTransform: 'uppercase',
        color: colors.textSecondary,
        margin: '0 0 8px 0',
      }}>
        {label}
      </p>
      <p style={{
        fontSize: '24px',
        fontWeight: 700,
        color: colors.primary,
        margin: 0,
      }}>
        {value}
      </p>
    </div>
  );
}

function TimelineEntry({ analysis, isLatest, colors }) {
  const date = new Date(analysis.date);
  const formattedDate = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  const confidenceEmoji = {
    high: '🟢',
    medium: '🟡',
    low: '🔴',
  }[analysis.confidence] || '⚪';

  return (
    <div style={{
      position: 'relative',
      paddingLeft: '48px',
      paddingBottom: '24px',
    }}>
      {/* Dot */}
      <div style={{
        position: 'absolute',
        left: '12px',
        top: '4px',
        width: '16px',
        height: '16px',
        borderRadius: '50%',
        backgroundColor: isLatest ? colors.primary : colors.surface,
        border: `2px solid ${isLatest ? colors.primary : colors.border}`,
      }} />

      {/* Content */}
      <div style={{
        backgroundColor: isLatest ? `${colors.primary}11` : 'transparent',
        borderRadius: '8px',
        padding: '12px',
        border: isLatest ? `1px solid ${colors.primary}` : 'none',
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '4px',
        }}>
          <p style={{
            fontSize: '12px',
            color: colors.textSecondary,
            margin: 0,
          }}>
            {formattedDate}
          </p>
          {isLatest && (
            <span style={{
              fontSize: '11px',
              fontWeight: 600,
              color: colors.primary,
              textTransform: 'uppercase',
            }}>
              Latest
            </span>
          )}
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <p style={{
            fontSize: '20px',
            fontWeight: 700,
            color: colors.text,
            margin: 0,
          }}>
            {analysis.body_fat_percentage}%
          </p>
          <span style={{ fontSize: '16px' }}>
            {confidenceEmoji}
          </span>
        </div>
      </div>
    </div>
  );
}
