// Centralized Auth Manager
const Auth = {
    // Save token securely
    setToken: (token) => {
        localStorage.setItem('token', token);
    },

    // Retrieve token for API requests
    getToken: () => {
        return localStorage.getItem('token');
    },

    // Check if user is logged in
    isAuthenticated: () => {
        return !!localStorage.getItem('token');
    },

    // Logout and clear state
    logout: () => {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
    },

    // Helper to get headers for API calls
    getHeaders: () => {
        const token = Auth.getToken();
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };
    },

    // Enforce login on protected pages
    protectRoute: () => {
        if (!Auth.isAuthenticated()) {
            window.location.href = 'login.html';
        }
    }
};