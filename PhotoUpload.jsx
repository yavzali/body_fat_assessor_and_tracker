/**
 * Photo Upload Widget
 * 
 * Allows users to drag and drop or select a photo for body composition analysis.
 */

import React, { useState, useRef } from 'react';
import { useHostState, useFileUpload, useTheme } from '../shared/hooks.js';
import { uploadPhoto, callTool, validateFile } from '../shared/api.js';

export default function PhotoUpload() {
  const { toolOutput, widgetState } = useHostState();
  const { isDragging, isUploading, setIsUploading, handlers } = useFileUpload();
  const { colors } = useTheme();
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);

  // Get user ID from widget state
  const userId = widgetState?.user_id || toolOutput?.structuredContent?.user_id;

  const handleFileSelect = (files) => {
    setError(null);

    if (!files || files.length === 0) {
      return;
    }

    const file = files[0];

    // Validate file
    const validation = validateFile(file);
    if (!validation.valid) {
      setError(validation.errors.join('. '));
      return;
    }

    // Set selected file and preview
    setSelectedFile(file);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    const files = handlers.onDrop(e);
    handleFileSelect(files);
  };

  const handleFileInputChange = (e) => {
    handleFileSelect(e.target.files);
  };

  const handleUploadClick = async () => {
    if (!selectedFile || !userId) {
      setError('No file selected or user not identified');
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadStatus('Uploading...');

    try {
      // Upload to server
      const uploadResult = await uploadPhoto(selectedFile, userId, 'front');

      setUploadStatus('Processing...');

      // Call process_photo tool with the photo ID
      await callTool('process_photo', { photo_id: uploadResult.photo_id });

      setUploadStatus('Analysis complete!');

    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Upload failed');
      setUploadStatus(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleClickUploadZone = () => {
    fileInputRef.current?.click();
  };

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '24px',
      maxWidth: '600px',
      margin: '0 auto',
      backgroundColor: colors.background,
      color: colors.text,
    }}>
      <h2 style={{ marginTop: 0, marginBottom: '8px', fontSize: '24px' }}>
        📸 Upload Photo
      </h2>
      <p style={{ color: colors.textSecondary, marginBottom: '24px', fontSize: '14px' }}>
        Upload a photo for body composition analysis. Your face will be automatically blurred.
      </p>

      {/* Upload Zone */}
      <div
        {...handlers}
        onDrop={handleDrop}
        onClick={handleClickUploadZone}
        style={{
          border: `2px dashed ${isDragging ? colors.primary : colors.border}`,
          borderRadius: '12px',
          padding: '40px',
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragging ? `${colors.primary}22` : colors.surface,
          transition: 'all 0.2s ease',
          marginBottom: '16px',
        }}
      >
        {preview ? (
          <div>
            <img
              src={preview}
              alt="Preview"
              style={{
                maxWidth: '100%',
                maxHeight: '300px',
                borderRadius: '8px',
                marginBottom: '16px',
              }}
            />
            <p style={{ color: colors.textSecondary, fontSize: '14px', margin: 0 }}>
              {selectedFile?.name}
            </p>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📷</div>
            <p style={{ fontSize: '16px', fontWeight: 500, margin: '0 0 8px 0' }}>
              {isDragging ? 'Drop your photo here' : 'Drag and drop your photo'}
            </p>
            <p style={{ color: colors.textSecondary, fontSize: '14px', margin: 0 }}>
              or click to select a file
            </p>
            <p style={{ color: colors.textSecondary, fontSize: '12px', marginTop: '8px' }}>
              Supported: JPG, PNG, WEBP (max 10MB)
            </p>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.webp"
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
        />
      </div>

      {/* Tips */}
      {!selectedFile && (
        <div style={{
          backgroundColor: colors.surface,
          padding: '16px',
          borderRadius: '8px',
          marginBottom: '16px',
        }}>
          <p style={{ fontSize: '14px', fontWeight: 500, margin: '0 0 8px 0' }}>
            📋 Tips for best results:
          </p>
          <ul style={{ 
            margin: 0, 
            paddingLeft: '20px', 
            fontSize: '13px',
            color: colors.textSecondary,
          }}>
            <li>Good, even lighting</li>
            <li>Stand 6-8 feet from camera</li>
            <li>Wear fitted clothing</li>
            <li>Front-facing, upright pose</li>
          </ul>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{
          backgroundColor: `${colors.error}22`,
          color: colors.error,
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '14px',
        }}>
          ❌ {error}
        </div>
      )}

      {/* Upload Status */}
      {uploadStatus && (
        <div style={{
          backgroundColor: `${colors.success}22`,
          color: colors.success,
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '14px',
        }}>
          ✅ {uploadStatus}
        </div>
      )}

      {/* Upload Button */}
      {selectedFile && !isUploading && !uploadStatus && (
        <button
          onClick={handleUploadClick}
          disabled={isUploading}
          style={{
            width: '100%',
            padding: '14px',
            backgroundColor: colors.primary,
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 600,
            cursor: isUploading ? 'not-allowed' : 'pointer',
            opacity: isUploading ? 0.6 : 1,
            transition: 'opacity 0.2s ease',
          }}
        >
          {isUploading ? 'Uploading & Analyzing...' : 'Upload & Analyze'}
        </button>
      )}

      {/* Privacy Note */}
      <p style={{
        fontSize: '12px',
        color: colors.textSecondary,
        textAlign: 'center',
        marginTop: '16px',
        marginBottom: 0,
      }}>
        🔒 Your privacy matters: Faces are automatically blurred before storage.
      </p>
    </div>
  );
}
