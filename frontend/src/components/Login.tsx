import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/axios';
import { AxiosError } from 'axios';

const Login: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            const response = await apiClient.post('/users/login/', {
                username,
                password,
            });
            login(response.data);
            navigate('/dashboard');
        } catch (err) {
            const error = err as AxiosError<{ error: string }>;
            if (error.response && error.response.data) {
                setError(error.response.data.error);
            } else {
                setError('Login failed. Please try again.');
            }
            console.error('Login failed', error);
        }
    };

    return (
        <form onSubmit={handleSubmit} className='flex flex-col gap-4'>
            <h2>Login</h2>
            {error && <p className="text-red-500">{error}</p>}
            <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                required
                className='border border-gray-300 rounded-md p-2 bg-gray-150'
            />
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className='border border-gray-300 rounded-md p-2 bg-gray-150'
            />
            <button type="submit" className='bg-blue-500 text-white p-2 rounded-md'>Login</button>
        </form>
    );
};

export default Login;
