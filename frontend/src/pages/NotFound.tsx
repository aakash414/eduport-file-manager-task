import React from 'react';
import { Link } from 'react-router-dom';

const NotFound: React.FC = () => {
    return (
        <div className="flex flex-col items-center justify-center h-screen bg-gray-100 text-center px-4">
            <h1 className="text-6xl font-bold text-gray-800">404</h1>
            <p className="text-2xl font-semibold text-gray-700 mt-4">Page Not Found</p>
            <p className="text-gray-500 mt-2">Sorry, the page you are looking for does not exist.</p>
            <Link to="/dashboard" className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                Go to Dashboard
            </Link>
        </div>
    );
};

export default NotFound;