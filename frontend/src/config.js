// Configuration for backend API URLs
const config = {
  // Development URLs
  development: {
    backendUrl: 'http://localhost:8000'
  },
  // Localtunnel URLs
  localtunnel: {
    backendUrl: 'https://ddb7-186-15-77-109.ngrok-free.app'
  },
  // Ngrok URLs
  ngrok: {
    backendUrl: 'https://ddb7-186-15-77-109.ngrok-free.app'
  }
};

// Set this to switch between environments
const currentEnv = 'ngrok'; // Change this to 'development', 'localtunnel', or 'ngrok'

export const API_BASE_URL = config[currentEnv].backendUrl; 