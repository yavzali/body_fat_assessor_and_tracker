/**
 * API utilities for communicating with the backend server.
 */

const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Upload a photo to the server.
 * 
 * @param {File} file - The image file to upload
 * @param {string} userId - User ID from widget state
 * @param {string} photoType - Type of photo (front/side/back)
 * @returns {Promise<Object>} Upload response with photo_id
 */
export async function uploadPhoto(file, userId, photoType = 'front') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('photo_type', photoType);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    headers: {
      'X-User-Id': userId,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Call an MCP tool via window.openai.
 * 
 * @param {string} toolName - Name of the tool to call
 * @param {Object} args - Tool arguments
 * @returns {Promise<Object>} Tool response
 */
export async function callTool(toolName, args = {}) {
  if (!window.openai?.callTool) {
    throw new Error('OpenAI bridge not available');
  }

  try {
    const result = await window.openai.callTool(toolName, args);
    return result;
  } catch (error) {
    console.error('Tool call failed:', error);
    throw error;
  }
}

/**
 * Get the server URL based on environment.
 * 
 * @returns {string} Server base URL
 */
export function getServerUrl() {
  // In production, this would be configured properly
  // For now, use localhost
  return API_BASE_URL.replace('/api', '');
}

/**
 * Validate file before upload.
 * 
 * @param {File} file - File to validate
 * @param {number} maxSize - Maximum file size in bytes
 * @param {string[]} allowedTypes - Allowed MIME types
 * @returns {Object} Validation result
 */
export function validateFile(file, maxSize = 10 * 1024 * 1024, allowedTypes = ['image/jpeg', 'image/png', 'image/webp']) {
  const errors = [];

  if (file.size > maxSize) {
    errors.push(`File size exceeds ${maxSize / 1024 / 1024}MB limit`);
  }

  if (!allowedTypes.includes(file.type)) {
    errors.push(`File type ${file.type} not allowed. Allowed: ${allowedTypes.join(', ')}`);
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
