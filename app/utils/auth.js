/**
 * Authentication utility functions for consistent token management
 * across all components
 */

/**
 * Check if user is properly authenticated with valid token
 * @param {Object} auth - AuthContext object
 * @returns {boolean} - True if authenticated
 */
export const isProperlyAuthenticated = (auth) => {
  return auth && auth.user && auth.token && auth.token !== 'null';
};

/**
 * Get authentication headers for API requests
 * @param {Object} auth - AuthContext object
 * @returns {Object} - Headers object
 */
export const getAuthHeaders = (auth) => {
  if (!isProperlyAuthenticated(auth)) {
    console.warn('Attempting to get auth headers without proper authentication');
    return {};
  }
  return auth.getAuthHeaders();
};

/**
 * Get JSON headers for API requests
 * @param {Object} auth - AuthContext object
 * @returns {Object} - Headers object
 */
export const getJsonHeaders = (auth) => {
  if (!isProperlyAuthenticated(auth)) {
    console.warn('Attempting to get JSON headers without proper authentication');
    return {
      'Content-Type': 'application/json',
    };
  }
  return auth.getJsonHeaders();
};

/**
 * Handle authentication errors consistently
 * @param {Response} response - Fetch response object
 * @param {Object} auth - AuthContext object
 * @param {Function} setError - Error state setter
 * @returns {boolean} - True if error was handled
 */
export const handleAuthError = (response, auth, setError) => {
  if (response.status === 401) {
    setError('Session expired. Please log in again.');
    if (auth.logout) {
      auth.logout();
    }
    return true;
  }
  return false;
};

/**
 * Validate authentication before making API calls
 * @param {Object} auth - AuthContext object
 * @param {Function} setError - Error state setter
 * @returns {boolean} - True if authentication is valid
 */
export const validateAuthBeforeRequest = (auth, setError) => {
  if (!isProperlyAuthenticated(auth)) {
    setError('Authentication required. Please log in again.');
    return false;
  }
  return true;
};

/**
 * Make an authenticated API request with comprehensive error handling
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @param {Object} auth - AuthContext object
 * @param {Function} setError - Error state setter
 * @param {Function} setLoading - Loading state setter
 * @returns {Promise<Object|null>} - Response data or null on error
 */
export const makeAuthenticatedRequest = async (
  url, 
  options = {}, 
  auth, 
  setError, 
  setLoading
) => {
  if (!isProperlyAuthenticated(auth)) {
    const errorMsg = 'Authentication required. Please log in again.';
    setError(errorMsg);
    return null;
  }

  try {
    setLoading(true);
    setError(null);

    const response = await fetch(url, {
      ...options,
      headers: {
        ...getJsonHeaders(auth),
        ...options.headers,
      },
    });

    if (response.ok) {
      const data = await response.json();
      return data;
    }

    // Handle specific HTTP status codes
    switch (response.status) {
      case 401:
        setError('Session expired. Please log in again.');
        // Trigger logout for authentication errors
        if (auth.logout) {
          auth.logout();
        }
        break;
      case 403:
        setError('Access denied. You do not have permission to access this resource.');
        break;
      case 404:
        setError('Resource not found. Please check the URL and try again.');
        break;
      case 500:
        setError('Server error. Please try again later or contact support.');
        break;
      case 502:
      case 503:
      case 504:
        setError('Service temporarily unavailable. Please try again later.');
        break;
      default:
        try {
          const errorData = await response.json();
          setError(errorData.error || `Request failed with status ${response.status}`);
        } catch {
          setError(`Request failed with status ${response.status}`);
        }
    }

    return null;
  } catch (error) {
    console.error('Request error:', error);
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      setError('Network error. Please check your connection and try again.');
    } else {
      setError(error.message || 'An unexpected error occurred. Please try again.');
    }
    
    return null;
  } finally {
    setLoading(false);
  }
};
