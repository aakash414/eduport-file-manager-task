import axios from 'axios';

// Function to get CSRF token from cookies
function getCookie(name: string): string | null {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    withCredentials: true, // Important for sending cookies
});

// Add a request interceptor to include the CSRF token
apiClient.interceptors.request.use((config) => {
    if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method)) {
        const csrfToken = getCookie('csrftoken');
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken;
        }
    }
    return config;
});

export default apiClient;
