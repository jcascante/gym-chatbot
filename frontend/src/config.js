// Configuration for backend API URLs
const config = {
  // Development URLs
  development: {
    backendUrl: 'http://localhost:8000'
  },
  // Localtunnel URLs
  localtunnel: {
    backendUrl: 'https://0b99-186-64-156-104.ngrok-free.app'
  },
  // Ngrok URLs
  ngrok: {
    backendUrl: 'https://0b99-186-64-156-104.ngrok-free.app'
  }
};

// Set this to switch between environments
const currentEnv = 'ngrok'; // Change this to 'development', 'localtunnel', or 'ngrok'

export const API_BASE_URL = config[currentEnv].backendUrl; 