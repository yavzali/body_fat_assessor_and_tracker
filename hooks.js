/**
 * Reusable React hooks for widgets.
 */

import { useState, useEffect } from 'react';

/**
 * Hook to access OpenAI host state.
 * 
 * @returns {Object} Host state (toolInput, toolOutput, widgetState, theme, displayMode)
 */
export function useHostState() {
  const [hostState, setHostState] = useState({
    toolInput: null,
    toolOutput: null,
    widgetState: null,
    theme: 'light',
    displayMode: 'normal',
  });

  useEffect(() => {
    if (window.openai) {
      // Get initial state
      const updateState = () => {
        setHostState({
          toolInput: window.openai.toolInput,
          toolOutput: window.openai.toolOutput,
          widgetState: window.openai.widgetState,
          theme: window.openai.theme || 'light',
          displayMode: window.openai.displayMode || 'normal',
        });
      };

      updateState();

      // Listen for state changes
      const interval = setInterval(updateState, 100);

      return () => clearInterval(interval);
    }
  }, []);

  return hostState;
}

/**
 * Hook to manage widget state.
 * 
 * @param {*} initialState - Initial state value
 * @returns {[*, Function]} Current state and setter function
 */
export function useWidgetState(initialState) {
  const [state, setState] = useState(initialState);

  const setWidgetState = (newState) => {
    setState(newState);
    if (window.openai?.setWidgetState) {
      window.openai.setWidgetState(newState);
    }
  };

  return [state, setWidgetState];
}

/**
 * Hook for file upload with drag and drop.
 * 
 * @returns {Object} Upload utilities
 */
export function useFileUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    return files;
  };

  return {
    isDragging,
    uploadProgress,
    isUploading,
    setUploadProgress,
    setIsUploading,
    handlers: {
      onDragEnter: handleDragEnter,
      onDragLeave: handleDragLeave,
      onDragOver: handleDragOver,
      onDrop: handleDrop,
    },
  };
}

/**
 * Hook for theme-aware styling.
 * 
 * @returns {Object} Theme utilities
 */
export function useTheme() {
  const { theme } = useHostState();

  const isDark = theme === 'dark';

  const colors = isDark ? {
    background: '#1a1a1a',
    surface: '#2a2a2a',
    border: '#3a3a3a',
    text: '#ffffff',
    textSecondary: '#a0a0a0',
    primary: '#4f9eff',
    success: '#4caf50',
    error: '#f44336',
    warning: '#ff9800',
  } : {
    background: '#ffffff',
    surface: '#f5f5f5',
    border: '#e0e0e0',
    text: '#000000',
    textSecondary: '#666666',
    primary: '#1976d2',
    success: '#4caf50',
    error: '#f44336',
    warning: '#ff9800',
  };

  return {
    isDark,
    colors,
  };
}
