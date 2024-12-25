import axios from 'axios';

// Default headers
const defaultHeaders = {
	Accept: 'application/json'
};

// Function to make an API request
const apiClient = async (url, method = 'GET', headers = {}, body = null) => {
	const requestOptions = {
		method, // HTTP method (GET, POST, PUT, DELETE)
		headers: {
			...defaultHeaders,
			...headers,
			...(body ? { 'Content-Type': 'application/json' } : {}) // Automatically set content-type for requests with a body
		},
		data: body ? JSON.stringify(body) : null // Axios uses 'data' instead of 'body' for POST/PUT
	};

	try {
		const response = await axios(url, requestOptions);
		return response.data; // Axios automatically parses JSON
	} catch (error) {
		console.error('API Request failed:', error);
		throw error;
	}
};

// Helper functions for different HTTP methods

export const apiGet = async (url, headers = {}) => {
	return apiClient(url, 'GET', headers);
};

export const apiPost = async (url, body, headers = {}) => {
	return apiClient(url, 'POST', headers, body);
};

export const apiPut = async (url, body, headers = {}) => {
	return apiClient(url, 'PUT', headers, body);
};

export const apiDelete = async (url, body = null, headers = {}) => {
	return apiClient(url, 'DELETE', headers, body);
};
